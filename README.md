# Game Analytics: Unlocking Tennis Data with SportRadar API

Pipeline: Sportradar Tennis v3 API -> Python (parse/flatten JSON) -> MySQL -> Streamlit dashboard.

## Setup
1. `pip install -r requirements.txt`
2. Get a trial key at https://console.sportradar.com/signup (Tennis v3).
3. Create tables: `mysql -u root -p < schema.sql`
4. Set environment variables:
   ```
   export SPORTRADAR_API_KEY=your_key
   export DB_URL="mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/tennis_db"
   ```
5. Load data: `python extract.py`
6. Run app: `streamlit run app.py`

## Files
- `schema.sql` - tables, keys, indexes
- `extract.py` - API calls (retry + rate-limit handling), JSON flattening, transactional upsert
- `queries.sql` - all required SQL queries (competitions, venues, rankings)
- `app.py` - Streamlit app (dashboard, search/filter, details, country analysis, leaderboards, explorer, SQL runner)

## Schema notes
Follows the brief. `competitor_rankings` also stores ranking_type, year, week and gender so the app can filter by week.
