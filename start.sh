#!/usr/bin/env bash
set -euo pipefail

gunicorn -w 4 -b 0.0.0.0:8080 job_search.app:app
