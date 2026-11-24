-- Tennis analytics schema (MySQL 8)
CREATE DATABASE IF NOT EXISTS tennis_db;
USE tennis_db;

CREATE TABLE IF NOT EXISTS categories (
    category_id   VARCHAR(50)  PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS competitions (
    competition_id   VARCHAR(50)  PRIMARY KEY,
    competition_name VARCHAR(100) NOT NULL,
    parent_id        VARCHAR(50)  NULL,
    type             VARCHAR(20)  NOT NULL,
    gender           VARCHAR(10)  NOT NULL,
    category_id      VARCHAR(50)  NULL,
    FOREIGN KEY (category_id) REFERENCES categories(category_id),
    INDEX idx_comp_category (category_id),
    INDEX idx_comp_parent (parent_id),
    INDEX idx_comp_type (type)
);

CREATE TABLE IF NOT EXISTS complexes (
    complex_id   VARCHAR(50)  PRIMARY KEY,
    complex_name VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS venues (
    venue_id     VARCHAR(50)  PRIMARY KEY,
    venue_name   VARCHAR(100) NOT NULL,
    city_name    VARCHAR(100) NOT NULL,
    country_name VARCHAR(100) NOT NULL,
    country_code CHAR(3)      NOT NULL,
    timezone     VARCHAR(100) NOT NULL,
    complex_id   VARCHAR(50)  NULL,
    FOREIGN KEY (complex_id) REFERENCES complexes(complex_id),
    INDEX idx_venue_complex (complex_id),
    INDEX idx_venue_country (country_name)
);

CREATE TABLE IF NOT EXISTS competitors (
    competitor_id VARCHAR(50)  PRIMARY KEY,
    name          VARCHAR(100) NOT NULL,
    country       VARCHAR(100) NOT NULL,
    country_code  CHAR(3)      NOT NULL,
    abbreviation  VARCHAR(10)  NOT NULL,
    INDEX idx_competitor_country (country)
);

-- ranking_type / year / week / gender are small additions to the brief's
-- schema so the app can filter by week (as in the sample UI).
CREATE TABLE IF NOT EXISTS competitor_rankings (
    rank_id            INT AUTO_INCREMENT PRIMARY KEY,
    `rank`             INT NOT NULL,
    movement           INT NOT NULL,
    points             INT NOT NULL,
    competitions_played INT NOT NULL,
    competitor_id      VARCHAR(50) NOT NULL,
    ranking_type       VARCHAR(20) NULL,
    year               INT NULL,
    week               INT NULL,
    gender             VARCHAR(10) NULL,
    FOREIGN KEY (competitor_id) REFERENCES competitors(competitor_id),
    INDEX idx_rank_competitor (competitor_id),
    INDEX idx_rank_rank (`rank`),
    INDEX idx_rank_week (year, week)
);
