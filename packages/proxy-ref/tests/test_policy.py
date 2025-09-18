# tests/test_policy.py

import pytest
from adfree_proxy.policy import AdfreePolicy, canonicalize_json

def test_canonicalize():
    data = {"b": 2, "a": {"d": 4, "c": 3}}
    canonical = canonicalize_json(data)
    assert canonical == b'{"a":{"c":3,"d":4},"b":2}'

def test_policy_validation():
    policy_data = {
        "version": "1",
        "mode": "strict",
        "max_ads_per_page": 3,
        "allow_redirects": False,
        "allow_iframes": ["self"],
        "blocked_domains": ["*.adserver.com"],
        "report_to": "https://report.example.com/adfree"
    }
    policy = AdfreePolicy.parse_obj(policy_data)
    assert policy.mode == "strict"
    assert policy.max_ads_per_page == 3