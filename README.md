# JOB_SEARCH_Code

## Location targeting rules

Primary targets:
1. Jacksonville, Florida
2. Remote jobs

Secondary targets:
3. Hybrid jobs tied to Jacksonville / Northeast Florida
4. Nearby Jacksonville metro area jobs (Ponte Vedra, Orange Park, St. Augustine, Fernandina Beach, Atlantic Beach, Neptune Beach, Jacksonville Beach)

## Strict behavior

- Prioritize Jacksonville on-site or Jacksonville hybrid roles.
- Include fully remote roles.
- Include hybrid roles only when Jacksonville or nearby metro tied.
- Exclude non-remote roles outside Florida.
- Exclude relocation-only roles outside Florida unless remote.
- Reject roles with `Data Entry` in the title.
- Reject remote roles that explicitly exclude Florida residents.

## Ranking priority

1. Jacksonville on-site or Jacksonville hybrid
2. Remote jobs open nationally or to Florida
3. Nearby Jacksonville metro
4. Other Florida jobs only when manually approved as exceptional

## UI quick filters

- Jacksonville Only
- Remote Only
- Jacksonville + Remote
- Hybrid Only
- Nearby Metro
- All Qualified

## Default home behavior

On app open, show only Jacksonville + Remote jobs.

## Database schema

The jobs table includes:
- `city`
- `state`
- `remote_type`
- `location_raw`
- `geo_priority_score`

See `job_search/schema.sql` and `job_search/scope.py` for implementation.

## Railway deployment notes

This repository already includes a root-level `start.sh` script that starts the web process:

```bash
./start.sh
```

If Railway still reports "Missing start.sh", the service is usually building from the wrong root directory or an older commit.

Checklist:

1. **Deploy latest commit** that includes `start.sh` at repository root.
2. **Set the Railway service root directory** to the repo root (`/`) rather than `job_search/`.
3. **Set a custom start command** in Railway service settings as fallback:
   ```bash
   ./start.sh
   ```
   or
   ```bash
   python3 -m job_search.app
   ```
4. Ensure `start.sh` has executable permissions (`chmod +x start.sh`) and uses LF line endings.

## Job ingestion API

This app now supports manual/API ingestion so qualified jobs can be loaded without scraping:

- `POST /ingest` with JSON body for one job object, a list of jobs, or `{ "jobs": [...] }`.
- `GET /api/jobs` to list stored jobs.

Required fields per job: `title`, `description`, `location_raw`.
Optional fields: `company`, `source`, `url`, `city`, `state`, `remote_type`, `manually_approved`.

Example:

```bash
curl -X POST http://localhost:8080/ingest \
  -H "Content-Type: application/json" \
  -d '{"title":"Data Analyst","description":"BI dashboard role","location_raw":"Jacksonville, FL","source":"manual"}'
```

Set `JOB_SEARCH_DB_PATH` to control where SQLite data is stored.
