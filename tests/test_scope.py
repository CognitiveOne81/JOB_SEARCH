from job_search.scope import Job, default_homepage_filter, evaluate_job, normalize_location


def test_normalize_location_examples():
    assert normalize_location("Jacksonville, FL").geo_bucket == "jacksonville_local"
    assert normalize_location("Remote - US").geo_bucket == "remote"
    assert normalize_location("Florida / Remote").remote_type == "remote_florida"
    assert normalize_location("Jacksonville / Hybrid").geo_bucket == "jacksonville_hybrid"


def test_reject_tampa_unless_manual_approval():
    job = Job(
        title="Business Intelligence Analyst",
        description="Build dashboard and data products",
        location_raw="Tampa, FL",
    )
    assert evaluate_job(job).qualified is False


def test_accept_jacksonville_and_remote_by_default():
    jax = Job(
        title="Data Analyst",
        description="AI dashboard work",
        location_raw="Jacksonville, FL",
    )
    remote = Job(
        title="BI Analyst",
        description="Business intelligence and dashboard ownership",
        location_raw="Remote - United States",
    )
    tampa = Job(
        title="Data Analyst",
        description="AI dashboard work",
        location_raw="Tampa, FL",
        manually_approved=True,
    )

    filtered = default_homepage_filter([jax, remote, tampa])
    assert len(filtered) == 2
    assert jax in filtered
    assert remote in filtered
    assert tampa not in filtered


def test_reject_remote_when_florida_excluded():
    job = Job(
        title="Data Analyst",
        description="Remote position, not open to Florida",
        location_raw="Remote - United States",
    )
    result = evaluate_job(job)
    assert not result.qualified


def test_reject_data_entry_title():
    job = Job(
        title="Data Entry Analyst",
        description="dashboard ai bi",
        location_raw="Jacksonville, FL",
    )
    assert not evaluate_job(job).qualified
