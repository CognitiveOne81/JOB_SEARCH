CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    company TEXT,
    description TEXT,
    city TEXT,
    state TEXT,
    remote_type TEXT,
    location_raw TEXT,
    geo_priority_score INTEGER DEFAULT 99,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
