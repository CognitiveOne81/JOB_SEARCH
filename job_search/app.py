from __future__ import annotations

import json
import os
from html import escape
from wsgiref.simple_server import make_server

from job_search.scope import Job, default_homepage_filter, evaluate_job


def _sample_jobs() -> list[dict[str, str | Job]]:
    return [
        {
            "job": Job(
                title="Senior Data Analyst",
                description="Build AI-enabled KPI dashboards for sales operations.",
                location_raw="Jacksonville, FL",
            ),
            "url": "https://jobs.example.com/senior-data-analyst-jax",
            "source": "LinkedIn",
        },
        {
            "job": Job(
                title="Business Intelligence Analyst",
                description="Own BI reporting, SQL pipelines, and stakeholder reporting.",
                location_raw="Remote - United States",
            ),
            "url": "https://jobs.example.com/business-intelligence-analyst-remote",
            "source": "Indeed",
        },
        {
            "job": Job(
                title="Data Analyst (Hybrid)",
                description="Create executive dashboards and support analytics initiatives.",
                location_raw="Jacksonville / Hybrid",
                remote_type="hybrid",
            ),
            "url": "https://jobs.example.com/data-analyst-hybrid-jax",
            "source": "Built In",
        },
        {
            "job": Job(
                title="Data Analyst",
                description="Remote role, not open to Florida.",
                location_raw="Remote - US",
            ),
            "url": "https://jobs.example.com/data-analyst-remote-us",
            "source": "Dice",
        },
    ]


def _render_homepage() -> bytes:
    jobs_with_meta = _sample_jobs()
    homepage_jobs = default_homepage_filter([entry["job"] for entry in jobs_with_meta])
    filtered = [item for item in jobs_with_meta if item["job"] in homepage_jobs]

    cards: list[str] = []
    source_names = sorted({str(item["source"]) for item in filtered})
    for index, item in enumerate(filtered):
        job = item["job"]
        result = evaluate_job(job)
        cards.append(
            f"""
            <article class="card" data-job-card data-job-index="{index}">
              <h3><a href="{escape(str(item['url']))}" target="_blank" rel="noopener noreferrer">{escape(job.title)}</a></h3>
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
    source_options = "\n".join(f"<li>{escape(name)}</li>" for name in source_names)
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

    <p class="ok">Health endpoint available at <code>/health</code> and <code>/healthz</code>.</p>
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
