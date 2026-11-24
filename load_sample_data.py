"""Load SAMPLE (synthetic) data shaped like the Sportradar Tennis v3 responses.

Use only while the real API is unreachable. All IDs start with 'sample:' and
players are named 'Sample Player N'. Re-run extract.py later to replace it.

Usage:
    export DB_URL="mysql+pymysql://root:PASSWORD@localhost:3306/tennis_db"
    python3 load_sample_data.py
"""
import logging
import random

from sqlalchemy import create_engine, text

import extract  # reuses parse_* functions and upsert()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
random.seed(42)

CATEGORIES = ["ATP", "WTA", "ITF Men", "ITF Women", "Challenger", "Davis Cup"]
COUNTRIES = [("Croatia", "HRV"), ("Chile", "CHL"), ("Spain", "ESP"), ("Argentina", "ARG"),
             ("Australia", "AUS"), ("France", "FRA"), ("Italy", "ITA"), ("India", "IND"),
             ("United States", "USA"), ("Germany", "DEU"), ("El Salvador", "SLV"),
             ("Brazil", "BRA")]


def sample_competitions() -> dict:
    items = []
    for ci, cat in enumerate(CATEGORIES):
        cat_id = f"sample:category:{ci}"
        gender = "women" if "WTA" in cat or "Women" in cat else "men"
        for pi in range(6):  # parent competitions
            parent_id = f"sample:competition:{ci}-{pi}"
            items.append({"id": parent_id, "name": f"{cat} Open {pi + 1}",
                          "type": "singles", "gender": gender,
                          "category": {"id": cat_id, "name": cat}})
            for si in range(3):  # sub-competitions
                items.append({"id": f"{parent_id}-{si}",
                              "name": f"{cat} Open {pi + 1} {'Doubles' if si else 'Qualifying'}",
                              "parent_id": parent_id,
                              "type": "doubles" if si else "singles", "gender": gender,
                              "category": {"id": cat_id, "name": cat}})
    return {"competitions": items}


def sample_complexes() -> dict:
    zones = {"Chile": "America/Santiago", "Spain": "Europe/Madrid",
             "Croatia": "Europe/Zagreb", "Australia": "Australia/Melbourne",
             "France": "Europe/Paris", "India": "Asia/Kolkata"}
    names = ["Nacional", "Central Park", "Rod Court Complex", "Lakeside", "Olympic Tennis Park"]
    items = []
    for i, name in enumerate(names):
        venues = []
        for j in range(random.randint(1, 3)):
            country, code = random.choice(
                [c for c in COUNTRIES if c[0] in zones] if name != "Nacional"
                else [("Chile", "CHL")])
            venues.append({"id": f"sample:venue:{i}-{j}", "name": f"{name} Court {j + 1}",
                           "city_name": f"{country} City", "country_name": country,
                           "country_code": code, "timezone": zones[country]})
        items.append({"id": f"sample:complex:{i}", "name": name, "venues": venues})
    return {"complexes": items}


def sample_rankings() -> dict:
    ranks = []
    points = 9000
    for r in range(1, 201):
        points = max(50, points - random.randint(20, 120))
        country, code = random.choice(COUNTRIES)
        ranks.append({"rank": r, "movement": random.choice([0, 0, 1, -1, 2, -2, 3]),
                      "points": points, "competitions_played": random.randint(8, 30),
                      "competitor": {"id": f"sample:competitor:{r}", "name": f"Sample Player {r}",
                                     "country": country, "country_code": code,
                                     "abbreviation": f"SP{r}"[:10]}})
    return {"rankings": [{"name": "ATP", "year": 2026, "week": 47, "gender": "men",
                          "competitor_rankings": ranks}]}


def main():
    engine = create_engine(extract.DB_URL)
    cats, comps = extract.parse_competitions(sample_competitions())
    complexes, venues = extract.parse_complexes(sample_complexes())
    competitors, rankings = extract.parse_rankings(sample_rankings())
    with engine.begin() as conn:
        extract.upsert(conn, "categories", cats, ["category_id", "category_name"])
        extract.upsert(conn, "competitions", comps,
                       ["competition_id", "competition_name", "parent_id", "type", "gender", "category_id"])
        extract.upsert(conn, "complexes", complexes, ["complex_id", "complex_name"])
        extract.upsert(conn, "venues", venues,
                       ["venue_id", "venue_name", "city_name", "country_name",
                        "country_code", "timezone", "complex_id"])
        extract.upsert(conn, "competitors", competitors,
                       ["competitor_id", "name", "country", "country_code", "abbreviation"])
        conn.execute(text("DELETE FROM competitor_rankings"))
        conn.execute(text(
            "INSERT INTO competitor_rankings (`rank`, movement, points, competitions_played, "
            "competitor_id, ranking_type, year, week, gender) VALUES "
            "(:rank, :movement, :points, :competitions_played, :competitor_id, "
            ":ranking_type, :year, :week, :gender)"), rankings)
    logging.info("SAMPLE data loaded: %d competitions, %d venues, %d rankings",
                 len(comps), len(venues), len(rankings))


if __name__ == "__main__":
    main()
