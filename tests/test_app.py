from job_search.app import app


def _call(path: str):
    captured = {}

    def start_response(status, headers):
        captured['status'] = status
        captured['headers'] = dict(headers)

    body = b''.join(app({'PATH_INFO': path}, start_response)).decode('utf-8')
    return captured['status'], captured['headers'], body


def test_homepage_renders_html_ui():
    status, headers, body = _call('/')
    assert status == '200 OK'
    assert headers['Content-Type'].startswith('text/html')
    assert 'Job Search Dashboard' in body


def test_health_endpoint_still_json():
    status, headers, body = _call('/health')
    assert status == '200 OK'
    assert headers['Content-Type'] == 'application/json'
    assert '"status": "ok"' in body
