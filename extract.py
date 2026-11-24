"""Fetch Sportradar Tennis v3 data and load it into MySQL.

Usage:
    export SPORTRADAR_API_KEY=xxxx
    export DB_URL="mysql+pymysql://root:password@localhost:3306/tennis_db"
    python extract.py
"""
import logging
import os
import time

import requests
from sqlalchemy import create_engine, text

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

API_KEY = os.environ.get("SPORTRADAR_API_KEY", "")
BASE_URL = "https://api.sportradar.com/tennis/trial/v3/en"
DB_URL = os.environ.get("DB_URL", "mysql+pymysql://root:password@localhost:3306/tennis_db")
REQUEST_GAP_SECONDS = 1.1  # trial keys allow ~1 request/second


def fetch(endpoint: str, retries: int = 3) -> dict:
    """GET an endpoint with retry/backoff for rate limits and network errors."""
    url = f"{BASE_URL}/{endpoint}.json"
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, params={"api_key": API_KEY}, timeout=30)
            if resp.status_code == 429:
                logging.warning("Rate limited on %s (attempt %d)", endpoint, attempt)
                time.sleep(2 * attempt)
                continue
            resp.raise_for_status()
            time.sleep(REQUEST_GAP_SECONDS)
            return resp.json()
        except requests.RequestException as exc:
            logging.warning("Request failed for %s: %s", endpoint, exc)
            time.sleep(2 * attempt)
    raise RuntimeError(f"Could not fetch {endpoint} after {retries} attempts")


# ---------- parsers: nested JSON -> flat rows ----------
def parse_competitions(data: dict):
    categories, competitions = {}, []
    for item in data.get("competitions", []):
        cat = item.get("category") or {}
        if cat.get("id"):
            categories[cat["id"]] = {"category_id": cat["id"],
                                     "category_name": cat.get("name", "Unknown")}
        competitions.append({
            "competition_id": item["id"],
            "competition_name": item.get("name", "Unknown"),
            "parent_id": item.get("parent_id"),
            "type": item.get("type", "unknown"),
            "gender": item.get("gender", "unknown"),
            "category_id": cat.get("id"),
        })
    return list(categories.values()), competitions


def parse_complexes(data: dict):
    complexes, venues = [], []
    for cx in data.get("complexes", []):
        complexes.append({"complex_id": cx["id"], "complex_name": cx.get("name", "Unknown")})
        for v in cx.get("venues", []):
            venues.append({
                "venue_id": v["id"],
                "venue_name": v.get("name", "Unknown"),
                "city_name": v.get("city_name", "Unknown"),
                "country_name": v.get("country_name", "Unknown"),
                "country_code": (v.get("country_code") or "UNK")[:3],
                "timezone": v.get("timezone", "Unknown"),
                "complex_id": cx["id"],
            })
    return complexes, venues


def parse_rankings(data: dict):
    competitors, rankings = {}, []
    for group in data.get("rankings", []):
        for cr in group.get("competitor_rankings", []):
            comp = cr.get("competitor") or {}
            if not comp.get("id"):
                continue
            competitors[comp["id"]] = {
                "competitor_id": comp["id"],
                "name": comp.get("name", "Unknown"),
                "country": comp.get("country", "Unknown"),
                "country_code": (comp.get("country_code") or "UNK")[:3],
                "abbreviation": comp.get("abbreviation", "N/A")[:10],
            }
            rankings.append({
                "rank": cr.get("rank", 0),
                "movement": cr.get("movement", 0),
                "points": cr.get("points", 0),
                "competitions_played": cr.get("competitions_played", 0),
                "competitor_id": comp["id"],
                "ranking_type": group.get("name"),
                "year": group.get("year"),
                "week": group.get("week"),
                "gender": group.get("gender"),
            })
    return list(competitors.values()), rankings


# ---------- loaders ----------
def upsert(conn, table: str, rows: list, columns: list):
    if not rows:
        logging.warning("No rows for %s", table)
        return
    cols = ", ".join(f"`{c}`" for c in columns)
    params = ", ".join(f":{c}" for c in columns)
    updates = ", ".join(f"`{c}`=VALUES(`{c}`)" for c in columns)
    conn.execute(text(f"INSERT INTO {table} ({cols}) VALUES ({params}) "
                      f"ON DUPLICATE KEY UPDATE {updates}"), rows)
    logging.info("Loaded %d rows into %s", len(rows), table)


def main():
    if not API_KEY:
        raise SystemExit("Set SPORTRADAR_API_KEY first.")
    engine = create_engine(DB_URL)

    cats, comps = parse_competitions(fetch("competitions"))
    complexes, venues = parse_complexes(fetch("complexes"))
    competitors, rankings = parse_rankings(fetch("double_competitors_rankings"))

    try:
        with engine.begin() as conn:  # single transaction: all or nothing
            upsert(conn, "categories", cats, ["category_id", "category_name"])
            upsert(conn, "competitions", comps,
                   ["competition_id", "competition_name", "parent_id", "type", "gender", "category_id"])
            upsert(conn, "complexes", complexes, ["complex_id", "complex_name"])
            upsert(conn, "venues", venues,
                   ["venue_id", "venue_name", "city_name", "country_name",
                    "country_code", "timezone", "complex_id"])
            upsert(conn, "competitors", competitors,
                   ["competitor_id", "name", "country", "country_code", "abbreviation"])
            conn.execute(text("DELETE FROM competitor_rankings"))  # snapshot reload
            conn.execute(text(
                "INSERT INTO competitor_rankings (`rank`, movement, points, competitions_played, "
                "competitor_id, ranking_type, year, week, gender) VALUES "
                "(:rank, :movement, :points, :competitions_played, :competitor_id, "
                ":ranking_type, :year, :week, :gender)"), rankings)
            logging.info("Loaded %d rows into competitor_rankings", len(rankings))
    except Exception:
        logging.exception("Database load failed; transaction rolled back")
        raise


if __name__ == "__main__":
    main()
