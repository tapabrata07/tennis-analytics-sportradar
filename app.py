"""Tennis Analytics Explorer - Streamlit app.  Run: streamlit run app.py"""
import os

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

DB_URL = os.environ.get("DB_URL", "mysql+pymysql://root:password@localhost:3306/tennis_db")

st.set_page_config(page_title="Tennis Explorer", page_icon="🎾", layout="wide")


@st.cache_resource
def get_engine():
    return create_engine(DB_URL, pool_pre_ping=True)


@st.cache_data(ttl=300)
def run_query(sql: str, params=None) -> pd.DataFrame:
    """Execute a read query; return a DataFrame (empty on error)."""
    try:
        with get_engine().connect() as conn:
            return pd.read_sql(text(sql), conn, params=params or {})
    except Exception as exc:
        st.error(f"Database error: {exc}")
        return pd.DataFrame()


RANKINGS_SQL = """
SELECT c.competitor_id, c.name, c.country, c.country_code, c.abbreviation,
       r.`rank`, r.movement, r.points, r.competitions_played, r.year, r.week
FROM competitor_rankings r JOIN competitors c ON r.competitor_id = c.competitor_id
"""

st.title("🎾 Tennis Analytics Explorer")
page = st.sidebar.radio("Navigate", [
    "Home Dashboard", "Search & Filter", "Competitor Details", "Country Analysis",
    "Leaderboards", "Competitions Explorer", "Venues & Complexes", "SQL Query Runner"])

# ---------------- Home ----------------
if page == "Home Dashboard":
    stats = run_query("""SELECT COUNT(DISTINCT c.competitor_id) AS competitors,
                                COUNT(DISTINCT c.country) AS countries,
                                MAX(r.points) AS max_points
                         FROM competitors c LEFT JOIN competitor_rankings r
                         ON r.competitor_id = c.competitor_id""")
    if not stats.empty:
        a, b, c = st.columns(3)
        a.metric("Total competitors", int(stats.competitors[0]))
        b.metric("Countries represented", int(stats.countries[0]))
        c.metric("Highest points", int(stats.max_points[0] or 0))
    left, right = st.columns(2)
    cat = run_query("""SELECT cat.category_name, COUNT(*) AS total FROM competitions c
                       JOIN categories cat ON c.category_id = cat.category_id
                       GROUP BY cat.category_name ORDER BY total DESC LIMIT 15""")
    left.subheader("Competitions by category")
    left.bar_chart(cat.set_index("category_name"))
    typ = run_query("""SELECT type, gender, COUNT(*) AS total FROM competitions
                       GROUP BY type, gender""")
    right.subheader("Competitions by type & gender")
    if not typ.empty:
        right.bar_chart(typ.pivot(index="type", columns="gender", values="total").fillna(0))

# ---------------- Search & Filter ----------------
elif page == "Search & Filter":
    df = run_query(RANKINGS_SQL)
    if not df.empty:
        st.sidebar.header("Filters")
        name = st.sidebar.text_input("Search by name")
        countries = st.sidebar.multiselect("Country", sorted(df.country.unique()))
        lo, hi = int(df["rank"].min()), int(df["rank"].max())
        rank_range = st.sidebar.slider("Rank range", lo, hi, (lo, hi))
        min_pts = st.sidebar.number_input("Minimum points", 0, int(df.points.max()), 0)
        out = df[df["rank"].between(*rank_range) & (df.points >= min_pts)]
        if name:
            out = out[out.name.str.contains(name, case=False, na=False)]
        if countries:
            out = out[out.country.isin(countries)]
        st.write(f"{len(out)} competitors match")
        st.dataframe(out.sort_values("rank"), use_container_width=True, hide_index=True)

# ---------------- Competitor Details ----------------
elif page == "Competitor Details":
    df = run_query(RANKINGS_SQL)
    if not df.empty:
        choice = st.selectbox("Competitor", sorted(df.name.unique()))
        row = df[df.name == choice].sort_values("rank").iloc[0]
        a, b, c, d = st.columns(4)
        a.metric("Rank", int(row["rank"]), delta=int(row.movement))
        b.metric("Points", int(row.points))
        c.metric("Competitions played", int(row.competitions_played))
        d.metric("Country", f"{row.country} ({row.country_code})")

# ---------------- Country Analysis ----------------
elif page == "Country Analysis":
    df = run_query("""SELECT c.country, COUNT(*) AS competitors,
                             ROUND(AVG(r.points),1) AS avg_points, SUM(r.points) AS total_points
                      FROM competitor_rankings r JOIN competitors c ON r.competitor_id = c.competitor_id
                      GROUP BY c.country ORDER BY competitors DESC""")
    st.dataframe(df, use_container_width=True, hide_index=True)
    if not df.empty:
        st.bar_chart(df.head(15).set_index("country")["competitors"])

# ---------------- Leaderboards ----------------
elif page == "Leaderboards":
    n = st.slider("Show top N", 5, 50, 10)
    df = run_query(RANKINGS_SQL)
    if not df.empty:
        l, r = st.columns(2)
        l.subheader("Top ranked")
        l.dataframe(df.sort_values("rank").head(n)[["rank", "name", "country", "points"]],
                    hide_index=True, use_container_width=True)
        r.subheader("Highest points")
        r.dataframe(df.sort_values("points", ascending=False).head(n)[["name", "country", "points", "rank"]],
                    hide_index=True, use_container_width=True)

# ---------------- Competitions Explorer ----------------
elif page == "Competitions Explorer":
    df = run_query("""SELECT c.competition_id, c.competition_name, c.parent_id, c.type, c.gender,
                             cat.category_name
                      FROM competitions c LEFT JOIN categories cat ON c.category_id = cat.category_id""")
    if not df.empty:
        st.sidebar.header("Filters")
        types = st.sidebar.multiselect("Type", sorted(df.type.unique()))
        genders = st.sidebar.multiselect("Gender", sorted(df.gender.unique()))
        cats = st.sidebar.multiselect("Category", sorted(df.category_name.dropna().unique()))
        top_only = st.sidebar.checkbox("Top-level only (no parent)")
        if types: df = df[df.type.isin(types)]
        if genders: df = df[df.gender.isin(genders)]
        if cats: df = df[df.category_name.isin(cats)]
        if top_only: df = df[df.parent_id.isna() | (df.parent_id == "")]
        st.write(f"{len(df)} competitions")
        page_size = 100
        pages = max(1, -(-len(df) // page_size))
        p = st.number_input("Page", 1, pages, 1)
        st.dataframe(df.iloc[(p - 1) * page_size: p * page_size], hide_index=True,
                     use_container_width=True)
        st.subheader("Parent → sub-competitions")
        hier = run_query("""SELECT p.competition_name AS parent, COUNT(*) AS sub_competitions
                            FROM competitions c JOIN competitions p ON c.parent_id = p.competition_id
                            GROUP BY p.competition_name ORDER BY sub_competitions DESC LIMIT 20""")
        st.dataframe(hier, hide_index=True, use_container_width=True)

# ---------------- Venues & Complexes ----------------
elif page == "Venues & Complexes":
    df = run_query("""SELECT v.venue_name, v.city_name, v.country_name, v.timezone, cx.complex_name
                      FROM venues v LEFT JOIN complexes cx ON v.complex_id = cx.complex_id""")
    if not df.empty:
        country = st.selectbox("Country", ["All"] + sorted(df.country_name.unique()))
        view = df if country == "All" else df[df.country_name == country]
        st.dataframe(view, hide_index=True, use_container_width=True)
        st.subheader("Venues per complex")
        per = df.groupby("complex_name").size().sort_values(ascending=False).head(15)
        st.bar_chart(per)

# ---------------- SQL Query Runner ----------------
else:
    PRESET = {
        "Competitions with category": "SELECT c.competition_name, c.type, cat.category_name FROM competitions c LEFT JOIN categories cat ON c.category_id=cat.category_id",
        "Competitions per category": "SELECT cat.category_name, COUNT(*) total FROM competitions c JOIN categories cat ON c.category_id=cat.category_id GROUP BY cat.category_name ORDER BY total DESC",
        "Doubles competitions": "SELECT * FROM competitions WHERE type='doubles'",
        "Top-level competitions": "SELECT * FROM competitions WHERE parent_id IS NULL OR parent_id=''",
        "Complexes with >1 venue": "SELECT cx.complex_name, COUNT(*) n FROM complexes cx JOIN venues v ON v.complex_id=cx.complex_id GROUP BY cx.complex_name HAVING n>1",
        "Venues by country": "SELECT country_name, COUNT(*) n FROM venues GROUP BY country_name ORDER BY n DESC",
        "Top 5 ranked": "SELECT c.name, c.country, r.`rank`, r.points FROM competitor_rankings r JOIN competitors c ON r.competitor_id=c.competitor_id WHERE r.`rank`<=5 ORDER BY r.`rank`",
        "Stable rank (movement = 0)": "SELECT c.name, r.`rank` FROM competitor_rankings r JOIN competitors c ON r.competitor_id=c.competitor_id WHERE r.movement=0 ORDER BY r.`rank`",
        "Competitors per country": "SELECT country, COUNT(*) n FROM competitors GROUP BY country ORDER BY n DESC",
    }
    pick = st.selectbox("Preset query", list(PRESET))
    st.code(PRESET[pick], language="sql")
    st.dataframe(run_query(PRESET[pick]), hide_index=True, use_container_width=True)
