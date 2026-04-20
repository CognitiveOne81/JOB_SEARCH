from __future__ import annotations

import json
import os
from html import escape
from wsgiref.simple_server import make_server

from job_search.scope import Job, default_homepage_filter, evaluate_job


def _sample_jobs() -> list[Job]:
    return [
        Job(
            title="Senior Data Analyst",
            description="Build AI-enabled KPI dashboards for sales operations.",
            location_raw="Jacksonville, FL",
        ),
        Job(
            title="Business Intelligence Analyst",
            description="Own BI reporting, SQL pipelines, and stakeholder reporting.",
            location_raw="Remote - United States",
        ),
        Job(
            title="Data Analyst (Hybrid)",
            description="Create executive dashboards and support analytics initiatives.",
            location_raw="Jacksonville / Hybrid",
            remote_type="hybrid",
        ),
        Job(
            title="Data Analyst",
            description="Remote role, not open to Florida.",
            location_raw="Remote - US",
        ),
    ]


def _render_homepage() -> bytes:
    jobs = _sample_jobs()
    filtered = default_homepage_filter(jobs)
    cards: list[str] = []
    for job in filtered:
        result = evaluate_job(job)
        cards.append(
            f"""
            <article class="card">
              <h3>{escape(job.title)}</h3>
              <p class="meta"><strong>Location:</strong> {escape(job.location_raw)} · <strong>Bucket:</strong> {escape(result.geo_bucket)}</p>
              <p>{escape(job.description)}</p>
            </article>
            """
        )

    cards_html = "\n".join(cards) if cards else "<p>No qualified jobs yet.</p>"
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
    .card {{ background: #111933; border: 1px solid #2b3a67; border-radius: .75rem; padding: 1rem; margin-bottom: .85rem; }}
    .card h3 {{ margin-top: 0; margin-bottom: .5rem; }}
    .meta {{ color: #bfdbfe; font-size: .92rem; }}
    .ok {{ margin-top: 1rem; color: #93c5fd; font-size: .92rem; }}
  </style>
</head>
<body>
  <main class="wrap">
    <h1>Job Search Dashboard</h1>
    <p class="sub">Default view: Jacksonville + Remote qualified opportunities.</p>
    <section class="filters" aria-label="Quick filters">
      <span class="chip">Jacksonville Only</span>
      <span class="chip">Remote Only</span>
      <span class="chip">Jacksonville + Remote</span>
      <span class="chip">Hybrid Only</span>
      <span class="chip">Nearby Metro</span>
      <span class="chip">All Qualified</span>
    </section>
    <section>
      {cards_html}
    </section>
    <p class="ok">Health endpoint available at <code>/health</code> and <code>/healthz</code>.</p>
  </main>
</body>
</html>
"""
    return html.encode("utf-8")


def app(environ, start_response):
    path = environ.get("PATH_INFO", "/")

    if path == "/":
        body = _render_homepage()
        start_response(
            "200 OK",
            [
                ("Content-Type", "text/html; charset=utf-8"),
                ("Content-Length", str(len(body))),
            ],
        )
        return [body]

    if path in {"/health", "/healthz"}:
        payload = {
            "status": "ok",
            "service": "job-search",
        }
        body = json.dumps(payload).encode("utf-8")
        start_response(
            "200 OK",
            [
                ("Content-Type", "application/json"),
                ("Content-Length", str(len(body))),
            ],
        )
        return [body]

    body = json.dumps({"error": "not_found", "path": path}).encode("utf-8")
    start_response(
        "404 Not Found",
        [
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(body))),
        ],
    )
    return [body]


def main() -> None:
    port = int(os.environ.get("PORT", "8080"))
    with make_server("0.0.0.0", port, app) as httpd:
        print(f"Serving on 0.0.0.0:{port}")
        httpd.serve_forever()


if __name__ == "__main__":
    main()
