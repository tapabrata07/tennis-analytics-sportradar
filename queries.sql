USE tennis_db;

-- ================= COMPETITIONS =================
-- 1) All competitions with category name
SELECT c.competition_id, c.competition_name, c.type, c.gender, cat.category_name
FROM competitions c LEFT JOIN categories cat ON c.category_id = cat.category_id;

-- 2) Number of competitions in each category
SELECT cat.category_name, COUNT(*) AS total_competitions
FROM competitions c JOIN categories cat ON c.category_id = cat.category_id
GROUP BY cat.category_name ORDER BY total_competitions DESC;

-- 3) All doubles competitions
SELECT * FROM competitions WHERE type = 'doubles';

-- 4) Competitions in a specific category (e.g., ITF Men)
SELECT c.* FROM competitions c JOIN categories cat ON c.category_id = cat.category_id
WHERE cat.category_name = 'ITF Men';

-- 5) Parent competitions and their sub-competitions
SELECT p.competition_name AS parent_competition, c.competition_name AS sub_competition
FROM competitions c JOIN competitions p ON c.parent_id = p.competition_id
ORDER BY parent_competition;

-- 6) Distribution of competition types by category
SELECT cat.category_name, c.type, COUNT(*) AS total
FROM competitions c JOIN categories cat ON c.category_id = cat.category_id
GROUP BY cat.category_name, c.type ORDER BY cat.category_name, total DESC;

-- 7) Top-level competitions (no parent)
SELECT * FROM competitions WHERE parent_id IS NULL OR parent_id = '';

-- ================= COMPLEXES & VENUES =================
-- 1) Venues with complex name
SELECT v.venue_name, v.city_name, v.country_name, cx.complex_name
FROM venues v LEFT JOIN complexes cx ON v.complex_id = cx.complex_id;

-- 2) Venues per complex
SELECT cx.complex_name, COUNT(v.venue_id) AS venue_count
FROM complexes cx LEFT JOIN venues v ON v.complex_id = cx.complex_id
GROUP BY cx.complex_id, cx.complex_name ORDER BY venue_count DESC;

-- 3) Venues in a specific country (e.g., Chile)
SELECT * FROM venues WHERE country_name = 'Chile';

-- 4) Venues and timezones
SELECT venue_name, timezone FROM venues;

-- 5) Complexes with more than one venue
SELECT cx.complex_name, COUNT(v.venue_id) AS venue_count
FROM complexes cx JOIN venues v ON v.complex_id = cx.complex_id
GROUP BY cx.complex_id, cx.complex_name HAVING COUNT(v.venue_id) > 1;

-- 6) Venues grouped by country
SELECT country_name, COUNT(*) AS venue_count, GROUP_CONCAT(venue_name SEPARATOR ', ') AS venues
FROM venues GROUP BY country_name ORDER BY venue_count DESC;

-- 7) All venues for a specific complex (e.g., Nacional)
SELECT v.* FROM venues v JOIN complexes cx ON v.complex_id = cx.complex_id
WHERE cx.complex_name = 'Nacional';

-- ================= RANKINGS =================
-- 1) Competitors with rank and points
SELECT c.name, c.country, r.`rank`, r.points
FROM competitor_rankings r JOIN competitors c ON r.competitor_id = c.competitor_id
ORDER BY r.`rank`;

-- 2) Top 5 ranked competitors
SELECT c.name, c.country, r.`rank`, r.points
FROM competitor_rankings r JOIN competitors c ON r.competitor_id = c.competitor_id
WHERE r.`rank` <= 5 ORDER BY r.`rank`;

-- 3) Stable rank (no movement)
SELECT c.name, c.country, r.`rank`
FROM competitor_rankings r JOIN competitors c ON r.competitor_id = c.competitor_id
WHERE r.movement = 0 ORDER BY r.`rank`;

-- 4) Total points from a specific country (e.g., Croatia)
SELECT c.country, SUM(r.points) AS total_points
FROM competitor_rankings r JOIN competitors c ON r.competitor_id = c.competitor_id
WHERE c.country = 'Croatia' GROUP BY c.country;

-- 5) Competitors per country
SELECT country, COUNT(*) AS competitor_count
FROM competitors GROUP BY country ORDER BY competitor_count DESC;

-- 6) Highest points in the current (latest) week
SELECT c.name, c.country, r.points, r.year, r.week
FROM competitor_rankings r JOIN competitors c ON r.competitor_id = c.competitor_id
WHERE (r.year, r.week) = (SELECT year, week FROM competitor_rankings
                          ORDER BY year DESC, week DESC LIMIT 1)
ORDER BY r.points DESC LIMIT 10;
