# Game Analytics: Unlocking Tennis Data with SportRadar API

Pipeline: Sportradar Tennis v3 API -> Python (parse/flatten JSON) -> MySQL -> Streamlit dashboard.
> **Data note:** The Sportradar API connection (api.sportradar.com) was blocked or reset on my network during development, so the database in this submission is filled with **synthetic sample data** using `load_sample_data.py`. The sample data uses the same JSON structure as the API and goes through the same parsing and loading code. `extract.py` is the real extraction script and has not yet been run successfully against the live API. Names such as "Sample Player" are fictional. Once the connection works, running `python extract.py` replaces the sample data with real data.

## Setup
1. `pip install -r requirements.txt`
2. Get a trial key at https://console.sportradar.com/signup (Tennis v3).
3. Create tables: `mysql -u root -p < schema.sql`
4. Set environment variables:
   ```
   export SPORTRADAR_API_KEY=your_key
   export DB_URL="mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/tennis_db"
   ```
5. 5. Load data:
   - Real data: `python extract.py` (needs a working API key and network connection)
   - Sample data (used in this submission): `python load_sample_data.py`
6. Run app: `streamlit run app.py`

## Files
- `schema.sql` - tables, keys, indexes
- `extract.py` - API calls (retry + rate-limit handling), JSON flattening, transactional upsert
- `queries.sql` - all required SQL queries (competitions, venues, rankings)
- `app.py` - Streamlit app (dashboard, search/filter, details, country analysis, leaderboards, explorer, SQL runner)

## Schema notes
Follows the brief. `competitor_rankings` also stores ranking_type, year, week and gender so the app can filter by week.
