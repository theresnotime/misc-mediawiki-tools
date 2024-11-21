import common_utils


def test_get_project_info_by_domain():
    title, wiki_domain = common_utils.get_project_info_by_domain("en.wikipedia.org")
    assert title == "Category:Wikimedia Foundation staff"
    assert wiki_domain == "en.wikipedia.org"


def test_get_wiki_domain_from_url():
    wiki_domain = common_utils.get_wiki_domain_from_url(
        "https://en.wikipedia.org/wiki/Category:Wikimedia Foundation staff"
    )
    assert wiki_domain == "en.wikipedia.org"
