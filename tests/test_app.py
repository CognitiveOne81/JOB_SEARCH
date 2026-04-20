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
