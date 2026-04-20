from __future__ import annotations

import json
import os
from wsgiref.simple_server import make_server


def app(environ, start_response):
    path = environ.get("PATH_INFO", "/")

    if path in {"/", "/health", "/healthz"}:
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
