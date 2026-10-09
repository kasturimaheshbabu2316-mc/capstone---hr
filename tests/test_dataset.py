"""Unit tests for dataset.py (Task T1)."""

import pytest
from dataset import (
    JOB_APPLICATIONS,
    CATEGORIES,
    STATUSES,
    compute_escalation_score,
    compute_escalation_threshold,
    get_application_by_id,
    ESCALATION_THRESHOLD_80TH,
)


def test_dataset_size():
    assert len(JOB_APPLICATIONS) >= 40
    assert len(JOB_APPLICATIONS) == 50


def test_category_distribution():
    cat_counts = {c: 0 for c in CATEGORIES}
    for r in JOB_APPLICATIONS:
        cat_counts[r["category"]] += 1
    for c, cnt in cat_counts.items():
        assert cnt >= 3, f"Category '{c}' has {cnt} records (< 3)"


def test_status_distribution():
    st_counts = {s: 0 for s in STATUSES}
    for r in JOB_APPLICATIONS:
        st_counts[r["status"]] += 1
    for s, cnt in st_counts.items():
        assert cnt >= 1, f"Status '{s}' has {cnt} records (< 1)"


def test_flagged_percentage():
    total = len(JOB_APPLICATIONS)
    flagged = sum(1 for r in JOB_APPLICATIONS if r["flagged_priority_review"])
    pct = (flagged / total) * 100
    assert 10.0 <= pct <= 30.0, f"Flagged % is {pct:.2f}%, outside [10%, 30%]"


def test_salary_ranges():
    for r in JOB_APPLICATIONS:
        sal = r["expected_salary_inr"]
        assert 300000 <= sal <= 3000000, f"Salary {sal} outside [3L, 30L]"


def test_escalation_score_boundaries():
    min_score = compute_escalation_score(flagged=False, days_since_created=0)
    max_score = compute_escalation_score(flagged=True, days_since_created=30)
    assert min_score == 0.0
    assert max_score == 1.0
    assert 0.0 < ESCALATION_THRESHOLD_80TH < 1.0


def test_lookup_helper():
    rec = get_application_by_id("APP-00001")
    assert rec is not None
    assert rec["record_id"] == "APP-00001"
    assert get_application_by_id("APP-99999") is None
