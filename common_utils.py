import common_regexes
import defaults
import re
import requests


def get_projects():
    """Get all projects with a sitelink to the staff category"""
    response = requests.get(
        "https://www.wikidata.org/w/rest.php/wikibase/v1/entities/items/Q7205263/sitelinks",
        headers=defaults.HEADERS,
    )
    json = response.json()
    return json


def get_wiki_domain_from_url(url):
    """Get the wiki domain from the URL"""
    match = re.search(common_regexes.wiki_domain_regex, url)
    if match:
        return match.group("wiki_domain")
    return None


def parse_project(projects, project):
    title = projects[project]["title"]
    url = projects[project]["url"]
    if url is None:
        return None, None
    wiki_domain = get_wiki_domain_from_url(url)
    return title, wiki_domain


def get_project_info_by_domain(wiki_domain):
    """Get the project info by the wiki domain"""
    projects = get_projects()
    for project in projects:
        title, domain = parse_project(projects, project)
        if domain == wiki_domain:
            return title, domain
