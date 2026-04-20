from __future__ import annotations

import json
import os
import sqlite3
from html import escape
from pathlib import Path
from typing import Any
from wsgiref.simple_server import make_server

from job_search.scope import Job, default_homepage_filter, evaluate_job


_DB_ENV_VAR = "JOB_SEARCH_DB_PATH"
_DEFAULT_DB_FILENAME = "job_search.db"


def _db_path() -> str:
    configured = os.environ.get(_DB_ENV_VAR)
    if configured:
        return configured
    return str(Path(__file__).resolve().parent.parent / _DEFAULT_DB_FILENAME)


def _schema_sql() -> str:
    schema_path = Path(__file__).with_name("schema.sql")
    return schema_path.read_text(encoding="utf-8")


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def _init_db() -> None:
    with _get_connection() as conn:
        conn.executescript(_schema_sql())


def _row_to_job(row: sqlite3.Row) -> Job:
    return Job(
        title=str(row["title"] or ""),
        description=str(row["description"] or ""),
        city=str(row["city"] or ""),
        state=str(row["state"] or ""),
        remote_type=str(row["remote_type"] or ""),
        location_raw=str(row["location_raw"] or ""),
    )


def _fetch_jobs() -> list[dict[str, str | Job]]:
    with _get_connection() as conn:
        rows = conn.execute(
            """
            SELECT title, description, city, state, remote_type, location_raw, source, url
            FROM jobs
            ORDER BY datetime(created_at) DESC, id DESC
            """
        ).fetchall()

    output: list[dict[str, str | Job]] = []
    for row in rows:
        output.append(
            {
                "job": _row_to_job(row),
                "url": str(row["url"] or ""),
                "source": str(row["source"] or "Unknown"),
            }
        )
    return output


def _target_company_connections() -> list[dict[str, str]]:
    return [
        {"company": "FIS", "url": "https://careers.fisglobal.com/"},
        {"company": "Citi", "url": "https://jobs.citi.com/"},
        {"company": "Fanatics", "url": "https://www.fanaticsinc.com/careers"},
        {"company": "Florida Blue", "url": "https://careers.floridablue.com/"},
        {"company": "Bank of America", "url": "https://careers.bankofamerica.com/"},
        {"company": "Deutsche Bank", "url": "https://careers.db.com/"},
        {"company": "CSX", "url": "https://www.csx.com/index.cfm/working-at-csx/"},
        {"company": "Mayo Clinic", "url": "https://jobs.mayoclinic.org/"},
        {"company": "Deloitte", "url": "https://www2.deloitte.com/us/en/careers.html"},
        {
            "company": "Intercontinental Exchange",
            "url": "https://www.ice.com/careers",
        },
    ]


def _render_homepage() -> bytes:
    jobs_with_meta = _fetch_jobs()
    homepage_jobs = default_homepage_filter([entry["job"] for entry in jobs_with_meta])
    filtered = [item for item in jobs_with_meta if item["job"] in homepage_jobs]

    cards: list[str] = []
    source_names = sorted({str(item["source"]) for item in filtered})
    for index, item in enumerate(filtered):
        job = item["job"]
        result = evaluate_job(job)
        url = str(item["url"])
        title = escape(job.title)
        if url:
            title_html = (
                f'<a href="{escape(url)}" target="_blank" rel="noopener noreferrer">{title}</a>'
            )
        else:
            title_html = title
        cards.append(
            f"""
            <article class="card" data-job-card data-job-index="{index}">
              <h3>{title_html}</h3>
              <p class="meta"><strong>Location:</strong> {escape(job.location_raw)} · <strong>Bucket:</strong> {escape(result.geo_bucket)} · <strong>Source:</strong> {escape(str(item['source']))}</p>
              <p>{escape(job.description)}</p>
              <div class="actions">
                <button type="button" data-action="applied">Move to Applied</button>
                <button type="button" data-action="trash" class="danger">Trash Irrelevant</button>
              </div>
            </article>
            """
        )

    cards_html = "\n".join(cards) if cards else "<p>No qualified jobs yet.</p>"
    source_options = "\n".join(f"<li>{escape(name)}</li>" for name in source_names) or "<li>None yet</li>"
    company_connections = "\n".join(
        (
            f'<li><a href="{escape(item["url"])}" target="_blank" '
            f'rel="noopener noreferrer">{escape(item["company"])}</a></li>'
        )
        for item in _target_company_connections()
    )
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Job Search UI</title>
  <style>
    :root {{ color-scheme: light dark; }}
    body {{ font-family: Arial, sans-serif; margin: 0; background: #0b1020; color: #eef2ff; }}
    .wrap {{ max-width: 980px; margin: 0 auto; padding: 2rem 1rem 4rem; }}
    h1 {{ margin: 0 0 .25rem; font-size: 1.8rem; }}
    .sub {{ margin: 0 0 1rem; color: #c7d2fe; }}
    .filters {{ display: flex; gap: .5rem; flex-wrap: wrap; margin: 1rem 0 1.25rem; }}
    .chip {{ background: #1d4ed8; color: #fff; border-radius: 999px; padding: .35rem .7rem; font-size: .85rem; }}
    .tabs {{ display: flex; gap: .75rem; margin: .25rem 0 1rem; }}
    .tab-button {{ background: transparent; color: #dbeafe; border: 1px solid #3b82f6; border-radius: .5rem; padding: .4rem .75rem; cursor: pointer; }}
    .tab-button.active {{ background: #1e40af; }}
    .card {{ background: #111933; border: 1px solid #2b3a67; border-radius: .75rem; padding: 1rem; margin-bottom: .85rem; }}
    .card h3 {{ margin-top: 0; margin-bottom: .5rem; }}
    .card h3 a {{ color: #93c5fd; text-decoration: none; }}
    .card h3 a:hover {{ text-decoration: underline; }}
    .meta {{ color: #bfdbfe; font-size: .92rem; }}
    .actions {{ display: flex; gap: .5rem; margin-top: .75rem; }}
    .actions button {{ border: 1px solid #3b82f6; border-radius: .5rem; background: #1e293b; color: #e2e8f0; padding: .35rem .55rem; cursor: pointer; }}
    .actions button.danger {{ border-color: #ef4444; color: #fecaca; }}
    .panel.hidden {{ display: none; }}
    details {{ margin-bottom: .9rem; border: 1px solid #2b3a67; border-radius: .5rem; padding: .5rem .75rem; background: #0f1730; }}
    details summary {{ cursor: pointer; color: #c7d2fe; }}
    .ok {{ margin-top: 1rem; color: #93c5fd; font-size: .92rem; }}
  </style>
</head>
<body>
  <main class="wrap">
    <h1>Job Search Dashboard</h1>
    <p class="sub">Default view: Jacksonville + Remote qualified opportunities.</p>

    <details>
      <summary>Sources pulled for these jobs</summary>
      <ul>
        {source_options}
      </ul>
    </details>

    <details open>
      <summary>Target company hiring page connections</summary>
      <ul>
        {company_connections}
      </ul>
    </details>

    <section class="filters" aria-label="Quick filters">
      <span class="chip">Jacksonville Only</span>
      <span class="chip">Remote Only</span>
      <span class="chip">Jacksonville + Remote</span>
      <span class="chip">Hybrid Only</span>
      <span class="chip">Nearby Metro</span>
      <span class="chip">All Qualified</span>
    </section>

    <nav class="tabs" aria-label="Job tabs">
      <button class="tab-button active" type="button" data-tab="open">Open Jobs</button>
      <button class="tab-button" type="button" data-tab="applied">Applied Jobs</button>
    </nav>

    <section id="tab-open" class="panel" data-panel="open">
      {cards_html}
    </section>

    <section id="tab-applied" class="panel hidden" data-panel="applied" aria-live="polite">
      <p id="empty-applied">No applied jobs yet.</p>
    </section>

    <p class="ok">Health endpoint available at <code>/health</code> and <code>/healthz</code>. Ingestion endpoint: <code>POST /ingest</code>.</p>
  </main>

  <script>
    (function () {{
      const tabButtons = document.querySelectorAll('[data-tab]');
      const panels = document.querySelectorAll('[data-panel]');
      const appliedPanel = document.querySelector('[data-panel="applied"]');
      const emptyApplied = document.getElementById('empty-applied');

      tabButtons.forEach((button) => {{
        button.addEventListener('click', () => {{
          const target = button.getAttribute('data-tab');
          tabButtons.forEach((btn) => btn.classList.toggle('active', btn === button));
          panels.forEach((panel) => panel.classList.toggle('hidden', panel.getAttribute('data-panel') !== target));
        }});
      }});

      document.querySelectorAll('[data-job-card]').forEach((card) => {{
        card.addEventListener('click', (event) => {{
          const target = event.target;
          if (!(target instanceof HTMLElement)) return;

          const action = target.getAttribute('data-action');
          if (!action) return;

          if (action === 'trash') {{
            card.remove();
          }}

          if (action === 'applied') {{
            appliedPanel.appendChild(card);
            emptyApplied.style.display = 'none';
          }}
        }});
      }});
    }})();
  </script>
</body>
</html>
"""
    return html.encode("utf-8")


def _read_json_body(environ: dict[str, Any]) -> Any:
    raw_length = environ.get("CONTENT_LENGTH") or "0"
    try:
        length = int(raw_length)
    except (TypeError, ValueError):
        length = 0

    body = environ["wsgi.input"].read(length) if length > 0 else b""
    if not body:
        return None
    return json.loads(body.decode("utf-8"))


def _job_from_payload(payload: dict[str, Any]) -> Job:
    return Job(
        title=str(payload.get("title", "")),
        description=str(payload.get("description", "")),
        city=str(payload.get("city", "")),
        state=str(payload.get("state", "")),
        remote_type=str(payload.get("remote_type", "")),
        location_raw=str(payload.get("location_raw", "")),
        manually_approved=bool(payload.get("manually_approved", False)),
    )


def _insert_jobs(payload: Any) -> dict[str, Any]:
    items = payload if isinstance(payload, list) else payload.get("jobs", [payload])
    if not isinstance(items, list):
        raise ValueError("Payload must be an object, list, or object with a jobs array")

    inserted = 0
    rejected: list[dict[str, str]] = []

    with _get_connection() as conn:
        for item in items:
            if not isinstance(item, dict):
                rejected.append({"title": "", "reason": "Invalid job payload"})
                continue

            job = _job_from_payload(item)
            if not job.title or not job.description or not job.location_raw:
                rejected.append({"title": job.title, "reason": "title, description, and location_raw are required"})
                continue

            result = evaluate_job(job)
            if not result.qualified:
                rejected.append({"title": job.title, "reason": result.reason})
                continue

            conn.execute(
                """
                INSERT INTO jobs (
                    title, company, description, city, state, remote_type,
                    location_raw, geo_priority_score, source, url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.title,
                    str(item.get("company", "")),
                    job.description,
                    job.city,
                    job.state,
                    job.remote_type,
                    job.location_raw,
                    result.geo_priority_score,
                    str(item.get("source", "manual")),
                    str(item.get("url", "")),
                ),
            )
            inserted += 1

    return {"inserted": inserted, "rejected": rejected}


def _json_response(start_response, status: str, payload: dict[str, Any]):
    body = json.dumps(payload).encode("utf-8")
    start_response(
        status,
        [
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(body))),
        ],
    )
    return [body]


def app(environ, start_response):
    _init_db()
    path = environ.get("PATH_INFO", "/")
    method = environ.get("REQUEST_METHOD", "GET").upper()

    if path == "/" and method == "GET":
        body = _render_homepage()
        start_response(
            "200 OK",
            [
                ("Content-Type", "text/html; charset=utf-8"),
                ("Content-Length", str(len(body))),
            ],
        )
        return [body]

    if path in {"/health", "/healthz"} and method == "GET":
        return _json_response(start_response, "200 OK", {"status": "ok", "service": "job-search"})

    if path == "/api/jobs" and method == "GET":
        jobs = _fetch_jobs()
        records = []
        for item in jobs:
            job = item["job"]
            result = evaluate_job(job)
            records.append(
                {
                    "title": job.title,
                    "description": job.description,
                    "location_raw": job.location_raw,
                    "source": item["source"],
                    "url": item["url"],
                    "geo_bucket": result.geo_bucket,
                    "qualified": result.qualified,
                }
            )
        return _json_response(start_response, "200 OK", {"count": len(records), "jobs": records})

    if path == "/ingest" and method == "POST":
        try:
            payload = _read_json_body(environ)
            if payload is None:
                return _json_response(start_response, "400 Bad Request", {"error": "Empty JSON payload"})
            result = _insert_jobs(payload)
            return _json_response(start_response, "200 OK", result)
        except json.JSONDecodeError:
            return _json_response(start_response, "400 Bad Request", {"error": "Invalid JSON payload"})
        except ValueError as exc:
            return _json_response(start_response, "400 Bad Request", {"error": str(exc)})

    return _json_response(start_response, "404 Not Found", {"error": "not_found", "path": path})


def main() -> None:
    port = int(os.environ.get("PORT", "8080"))
    with make_server("0.0.0.0", port, app) as httpd:
        print(f"Serving on 0.0.0.0:{port}")
        httpd.serve_forever()


if __name__ == "__main__":
    main()
