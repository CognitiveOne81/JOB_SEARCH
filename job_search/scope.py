from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

REQUIRED_KEYWORDS = {
    "data",
    "ai",
    "bi",
    "dashboard",
    "business intelligence",
    "analyst",
}

EXCLUDED_TITLE_PHRASE = "data entry"

JACKSONVILLE_CITY = "jacksonville"
JACKSONVILLE_STATE = "fl"

NEARBY_METRO_CITIES = {
    "ponte vedra",
    "orange park",
    "st. augustine",
    "fernandina beach",
    "atlantic beach",
    "neptune beach",
    "jacksonville beach",
}

REMOTE_PATTERNS = {
    "remote",
    "fully remote",
    "work from home",
    "us remote",
    "remote - florida",
    "remote - east coast",
    "remote - united states",
    "remote - us",
}

REMOTE_EXCLUSION_PATTERNS = {
    "florida not eligible",
    "not open to florida",
    "excluding florida",
    "fl residents excluded",
}

# Home page quick filters
QUICK_FILTERS = [
    "Jacksonville Only",
    "Remote Only",
    "Jacksonville + Remote",
    "Hybrid Only",
    "Nearby Metro",
    "All Qualified",
]


@dataclass
class Job:
    title: str
    description: str
    city: str = ""
    state: str = ""
    remote_type: str = ""
    location_raw: str = ""
    manually_approved: bool = False


@dataclass
class LocationNormalization:
    city: str
    state: str
    remote_type: str
    geo_bucket: str


@dataclass
class EvaluationResult:
    qualified: bool
    reason: str
    geo_priority_score: int
    geo_bucket: str


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def normalize_location(location_raw: str) -> LocationNormalization:
    raw = normalize_text(location_raw)

    if any(p in raw for p in REMOTE_PATTERNS) or raw in {"remote", "wfh"}:
        if "florida" in raw:
            remote_type = "remote_florida"
        elif "east coast" in raw:
            remote_type = "remote_east_coast"
        else:
            remote_type = "remote_us"
        return LocationNormalization(city="", state="", remote_type=remote_type, geo_bucket="remote")

    if "jacksonville" in raw and "hybrid" in raw:
        return LocationNormalization(
            city="Jacksonville",
            state="FL",
            remote_type="hybrid",
            geo_bucket="jacksonville_hybrid",
        )

    if "jacksonville" in raw:
        return LocationNormalization(
            city="Jacksonville",
            state="FL",
            remote_type="onsite",
            geo_bucket="jacksonville_local",
        )

    for metro in NEARBY_METRO_CITIES:
        if metro in raw:
            return LocationNormalization(city=metro.title(), state="FL", remote_type="onsite", geo_bucket="nearby_metro")

    if re.search(r"\b([a-z\s]+),\s*fl\b", raw):
        city = re.search(r"\b([a-z\s]+),\s*fl\b", raw).group(1).strip().title()
        return LocationNormalization(city=city, state="FL", remote_type="onsite", geo_bucket="other_florida")

    return LocationNormalization(city="", state="", remote_type="onsite", geo_bucket="other")


def has_required_keywords(text: str) -> bool:
    text_norm = normalize_text(text)
    return any(keyword in text_norm for keyword in REQUIRED_KEYWORDS)


def should_reject_remote(location_raw: str, description: str) -> bool:
    txt = normalize_text(f"{location_raw} {description}")
    return any(pattern in txt for pattern in REMOTE_EXCLUSION_PATTERNS)


def score_geo_priority(normalized: LocationNormalization, manually_approved: bool = False) -> int:
    if normalized.geo_bucket in {"jacksonville_local", "jacksonville_hybrid"}:
        return 1
    if normalized.geo_bucket == "remote":
        return 2
    if normalized.geo_bucket == "nearby_metro":
        return 3
    if normalized.geo_bucket == "other_florida" and manually_approved:
        return 4
    return 99


def evaluate_job(job: Job) -> EvaluationResult:
    if EXCLUDED_TITLE_PHRASE in normalize_text(job.title):
        return EvaluationResult(False, "Excluded title: Data Entry", 99, "excluded")

    if not has_required_keywords(f"{job.title} {job.description}"):
        return EvaluationResult(False, "Missing required search keywords", 99, "excluded")

    normalized = normalize_location(job.location_raw or f"{job.city}, {job.state}")

    if normalized.geo_bucket == "remote" and should_reject_remote(job.location_raw, job.description):
        return EvaluationResult(False, "Remote role excludes Florida residents", 99, "excluded")

    score = score_geo_priority(normalized, manually_approved=job.manually_approved)
    if score == 99:
        return EvaluationResult(False, "Outside allowed location scope", score, normalized.geo_bucket)

    # Hybrid jobs are only valid for Jacksonville/Northeast Florida.
    if normalize_text(job.remote_type) == "hybrid" and normalized.geo_bucket not in {
        "jacksonville_hybrid",
        "jacksonville_local",
        "nearby_metro",
    }:
        return EvaluationResult(False, "Hybrid role is not tied to Jacksonville/Northeast Florida", 99, normalized.geo_bucket)

    return EvaluationResult(True, "Qualified", score, normalized.geo_bucket)


def default_homepage_filter(jobs: Iterable[Job]) -> list[Job]:
    """Show Jacksonville + Remote by default."""
    output: list[Job] = []
    for job in jobs:
        result = evaluate_job(job)
        if not result.qualified:
            continue
        if result.geo_bucket in {"jacksonville_local", "jacksonville_hybrid", "remote"}:
            output.append(job)
    return output
