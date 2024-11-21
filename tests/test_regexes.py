import common_regexes
import pytest
import re

lock_reason_match = [
    "No longer works at WMF",
    "No longer working for the Foundation",
    "No longer works here",
    "laid off",
    "laid-off",
    "offboarding",
    "off-boarding",
    "off boarding",
    "No longer employed at WMF",
    "No longer employed for us",
    "No longer employed with WMF" "No longer with WMF",
    "WMF Contractor; Contract ended.",
]
lock_reason_doesnt_match = [
    "Fox",
    "Oh no, it's a fox!",
    "Renamed",
    "Old account",
    "Old Foundation account",
    "Long-term abuse",
    "Spam-only account",
    "Cross-wiki abuse",
    "relocking per temp unlock last week",
]
category_match = [
    "[[Category:Wikimedia Foundation staff]]",
]


@pytest.mark.parametrize("match_string", lock_reason_match)
def test_lock_reason_regex_matches(match_string):
    assert re.search(common_regexes.commentRegex, match_string) is not None


@pytest.mark.parametrize("no_match_string", lock_reason_doesnt_match)
def test_lock_reason_regex_doesnt_match(no_match_string):
    assert re.search(common_regexes.commentRegex, no_match_string) is None


@pytest.mark.parametrize("match_string", category_match)
def test_category_regex_matches(match_string):
    assert re.search(common_regexes.categoryRegex, match_string) is not None
