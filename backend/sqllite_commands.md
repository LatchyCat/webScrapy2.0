-- First connect to your database
.open instance/charleston_news.db

-- See all tables
.tables

-- See schema for the articles table
.schema articles

-- See all columns from articles
PRAGMA table_info(articles);

-- Count total articles
SELECT COUNT(*) FROM articles;

-- See the most recent 5 articles
SELECT id, title, date, created_at FROM articles ORDER BY created_at DESC LIMIT 5;

-- Check content of a specific article
SELECT title, content, date FROM articles WHERE id = 1;

-- See articles ordered by date
SELECT id, title, date FROM articles ORDER BY date DESC LIMIT 5;

-- Check for any NULL values in important fields
SELECT id, title FROM articles WHERE title IS NULL OR content IS NULL;

-- Get size of content for each article
SELECT id, title, length(content) as content_length FROM articles ORDER BY content_length DESC LIMIT 5;

-- Export results to CSV for easier viewing
.mode csv
.output articles.csv
SELECT * FROM articles;
.output stdout
