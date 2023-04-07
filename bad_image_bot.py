import re

import requests
from pwiki.wiki import Wiki

import config

wiki = Wiki("meta.wikimedia.org", "TNTBot", config.TNT_BOT_BADIMAGE_PASS)
page = "MediaWiki:Bad image list"
filename = re.compile(r"\[\[:?.*?:(?P<file>.*?\..*?)\]\]")
bad_images = []


def get_all_sites() -> list:
    response = requests.get("https://wm-domains.toolforge.org/domains.json")
    json = response.json()
    return json["domains"]


def get_bad_images(site: str, bad_images: list) -> list:
    response = requests.get(
        f"https://{site}/w/api.php?action=parse&format=json&page={page}&prop=wikitext&formatversion=2"
    )

    json = response.json()
    if "error" in json:
        print(f"Error: {json['error']['info']}")
        return

    wikitext = json["parse"]["wikitext"]
    for line in wikitext.splitlines():
        matches = re.search(filename, line)
        if matches:
            bad_images.append(matches.group("file"))
    return bad_images


if __name__ == "__main__":
    sites = get_all_sites()
    for site in sites:
        print(site)
        if get_bad_images(site, bad_images) is not None:
            bad_images = get_bad_images(site, bad_images)
    print(len(bad_images))
