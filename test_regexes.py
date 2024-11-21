import pytest
import re
import regexes

match_these_strings = [
    "off-boarding",
    "no longer works at WMF",
    "no longer works for the foundation",
    "no longer works here",
    "laid off",
    "offboarding",
    "no longer employed at WMF",
    "no longer employed for us",
]
dont_match_these_strings = [
    "Fox",
    "Oh no, it's a fox!",
    "Renamed",
    "Old account",
    "Old Foundation account",
]


@pytest.mark.parametrize("match_string", match_these_strings)
def test_regex_matches(match_string):
    assert re.search(regexes.commentRegex, match_string) is not None


@pytest.mark.parametrize("no_match_string", dont_match_these_strings)
def test_regex_doesnt_match(no_match_string):
    assert re.search(regexes.commentRegex, no_match_string) is None
