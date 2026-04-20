from __future__ import annotations

from io import BytesIO

from job_search.app import app


def _call(path: str, method: str = 'GET', body: bytes = b''):
    captured = {}

    def start_response(status, headers):
        captured['status'] = status
        captured['headers'] = dict(headers)

    environ = {
        'PATH_INFO': path,
        'REQUEST_METHOD': method,
        'CONTENT_LENGTH': str(len(body)),
        'wsgi.input': BytesIO(body),
    }
    response_body = b''.join(app(environ, start_response)).decode('utf-8')
    return captured['status'], captured['headers'], response_body


def test_homepage_renders_html_ui():
    status, headers, body = _call('/')
    assert status == '200 OK'
    assert headers['Content-Type'].startswith('text/html')
    assert 'Job Search Dashboard' in body


def test_homepage_includes_target_company_hiring_links():
    status, headers, body = _call('/')
    assert status == '200 OK'
    assert headers['Content-Type'].startswith('text/html')
    assert 'Target company hiring page connections' in body
    assert 'https://careers.fisglobal.com/' in body
    assert 'https://jobs.citi.com/' in body
    assert 'https://www.fanaticsinc.com/careers' in body
    assert 'https://careers.floridablue.com/' in body
    assert 'https://careers.bankofamerica.com/' in body
    assert 'https://careers.db.com/' in body
    assert 'https://www.csx.com/index.cfm/working-at-csx/' in body
    assert 'https://jobs.mayoclinic.org/' in body
    assert 'https://www2.deloitte.com/us/en/careers.html' in body
    assert 'https://www.ice.com/careers' in body


def test_health_endpoint_still_json():
    status, headers, body = _call('/health')
    assert status == '200 OK'
    assert headers['Content-Type'] == 'application/json'
    assert '"status": "ok"' in body


def test_ingest_and_api_jobs_flow():
    payload = b'{"title":"Data Analyst","description":"BI dashboard role","location_raw":"Jacksonville, FL","source":"manual","url":"https://example.com/job"}'
    ingest_status, ingest_headers, ingest_body = _call('/ingest', method='POST', body=payload)
    assert ingest_status == '200 OK'
    assert ingest_headers['Content-Type'] == 'application/json'
    assert '"inserted": 1' in ingest_body

    jobs_status, jobs_headers, jobs_body = _call('/api/jobs')
    assert jobs_status == '200 OK'
    assert jobs_headers['Content-Type'] == 'application/json'
    assert '"count":' in jobs_body
    assert 'Data Analyst' in jobs_body
