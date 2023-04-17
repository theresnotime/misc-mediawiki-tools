import argparse
import datetime
import json
import os
import re
import sys
import time
from difflib import unified_diff

import requests
from pwiki.wiki import Wiki

import config
import regexes

# Config
SW_VERSION = "0.1.0"
EXCEPTIONS = [
    "User:WMF Legal",
    "User:Emergency",
    "User:WMFOffice",
    "User:Ops Monitor (WMF)",
]
CATEGORY = "Category:Wikimedia Foundation staff"
HEADERS = {"User-Agent": "TNTBot (https://meta.wikimedia.org/wiki/User:TNTBot)"}
DELAY = 15
SUMMARY = "([[:m:User:TNTBot#Marking_former_WMF_staff_accounts|automated]]) Marking user as former staff — many thanks, and best wishes for the future."


def get_staff_accounts(wiki: Wiki) -> list[str]:
    """Get a list of staff accounts from the category page"""
    wiki.purge(CATEGORY)
    time.sleep(3)
    return wiki.category_members(CATEGORY, ["User"])


def validate_user(user: str):
    """Validate a user name (i.e. a user page)"""
    return re.search(regexes.userRegex, user)


def get_lock_status(user: str) -> bool | dict:
    """Get the lock status of a user"""
    response = requests.get(
        f"https://meta.wikimedia.org/w/api.php?action=query&format=json&meta=globaluserinfo&formatversion=2&guiuser={user}",
        headers=HEADERS,
    )
    json = response.json()
    if "error" in json:
        print(f"Error: {json['error']['info']}")
        return False
    return json["query"]["globaluserinfo"]


def get_lock_event(user: str) -> bool | dict:
    """Get the lock event of a user"""
    response = requests.get(
        f"https://meta.wikimedia.org/w/api.php?action=query&format=json&list=logevents&formatversion=2&letype=globalauth&letitle={user}%40global&lelimit=1",
        headers=HEADERS,
    )
    json = response.json()
    if "error" in json:
        print(f"Error: {json['error']['info']}")
        return False
    if len(json["query"]["logevents"]) == 0:
        return False  # https://w.wiki/6bLq ??
    return json["query"]["logevents"][0]


def check_lock_reason(reason: str):
    """Check if the lock reason matches the regex"""
    return re.search(regexes.commentRegex, reason)


def check_cache(cache_file: str, user: str) -> bool:
    """Check if a user is in the cache file"""
    if os.path.isfile(cache_file):
        unlocked_cache = open(cache_file, "r")
        unlocked_accounts = json.loads(unlocked_cache.read())
        unlocked_cache.close()
        if user in unlocked_accounts:
            return True
    return False


def modification_date(filename: str) -> datetime:
    """Get the modification date of a file"""
    t = os.path.getmtime(filename)
    return datetime.datetime.fromtimestamp(t)


def rm_formerstaff(page_content: str) -> str:
    """Remove the {{former staff}} template from a page"""
    return regexes.fsRegex.sub("", page_content)


def rm_category(page_content: str) -> str:
    """Remove the category from a page"""
    return regexes.categoryRegex.sub("", page_content)


def add_formerparam(page_content: str) -> str:
    """Add the |former=yes parameter to the {{user info}} template"""
    return regexes.userinfoRegex.sub("{{user info\n| former = true", page_content)


def cleanup_params(page_content: str) -> str:
    """Cleanup parameters"""
    return regexes.cleanupRegex.sub("", page_content)


def modify_user_page(wiki: Wiki, user: str, page_content: str) -> str:
    """Modify a user page"""
    old_content = page_content
    new_content = rm_formerstaff(page_content)
    new_content = rm_category(new_content)
    new_content = cleanup_params(new_content)
    new_content = add_formerparam(new_content)
    diff = unified_diff(old_content.splitlines(1), new_content.splitlines(1))
    if DRY is False:
        wiki.edit(title=user, text=new_content, summary=SUMMARY)
        print(f" - {user}: Edited page and left the following summary: {SUMMARY}")
    else:
        print(
            f" - {user}: Would have edited page and left the following summary: {SUMMARY}"
        )
    if VIEW_DIFF is True:
        print("Diff:")
        sys.stdout.writelines(diff)
        print("\n----\n")
    if DRY is False:
        print(f"Sleeping for {DELAY} seconds...")
        time.sleep(DELAY)
    return new_content


if __name__ == "__main__":
    print(f"WMF Staff Accounts helper, v{SW_VERSION}")
    parser = argparse.ArgumentParser(
        prog="wmf-staff-accounts",
        description="WMF Staff Accounts helper, v" + SW_VERSION,
    )
    parser.add_argument(
        "-w",
        "--wiki",
        required=True,
        help="The wiki domain to run on",
        default="meta.wikimedia.org",
    )
    parser.add_argument("--diff", help="Show diff", action="store_true")
    parser.add_argument(
        "--cache-only", help="Only cache, do not make changes", action="store_true"
    )
    parser.add_argument(
        "--yes", help="Skip confirmation before start", action="store_true"
    )
    parser.add_argument("--regen-cache", help="Regenerate cache", action="store_true")
    parser.add_argument("--dry", help="Don't make any edits", action="store_true")
    parser.add_argument("-v", "--verbose", help="Be verbose", action="store_true")
    args = parser.parse_args()
    DRY = args.dry
    VIEW_DIFF = args.diff
    wiki_domain = args.wiki
    cache_only = args.cache_only
    verbose = args.verbose

    # Init
    wiki = Wiki(wiki_domain, "TNTBot", config.TNT_BOT_PASS)
    cache_file = f"{wiki_domain}_unlocked_accounts.json"

    # Print settings
    print(f"Running on https://{wiki_domain}")
    if args.regen_cache:
        if os.path.isfile(cache_file):
            print(f"I will regenerate cache file '{cache_file}'...")
            os.remove(cache_file)
    if cache_only:
        print(
            "Cache-only mode enabled: Locked accounts will be ignored, and no edits will be made."
        )
        DRY = True  # Not needed, but just in case
    else:
        if DRY:
            print("Dry run mode enabled: No edits will be made.")
        else:
            print("NOTICE: Edits will be made.")
            # Panic delay
            time.sleep(2)

    # Start
    print(f"Purging {CATEGORY} and getting staff accounts...")
    staff_accounts = get_staff_accounts(wiki)
    unlocked_accounts = []
    locked_accounts = []
    edited_accounts = []
    cached_accounts = []
    excluded_accounts = []

    print(f"Got {len(staff_accounts)} staff accounts. Checking cache file...")

    if os.path.isfile(cache_file):
        print(f"Cache file found: {cache_file}")
        print(f"Cache file last modified: {modification_date(cache_file)}")
        if datetime.datetime.now() - modification_date(cache_file) > datetime.timedelta(
            hours=12
        ):
            print("Cache file is older than 12 hours, deleting...")
            os.remove(cache_file)
        else:
            print("Cache file is less than 12 hours old — OK to use.")
    else:
        print("No cache file found — will create one.")

    if args.yes is False:
        input("\nPress Enter to continue...")
    print("\nChecking staff accounts, please wait...")
    print("")

    for user in staff_accounts:
        if verbose:
            print(f" - {user}: checking...")
        if validate_user(user) is not None:
            print(f" - {user}: not a user page")
            continue
        if user in EXCEPTIONS:
            excluded_accounts.append(user)
            print(f" - {user}: in exceptions list")
            continue
        if check_cache(cache_file, user) is True:
            cached_accounts.append(user)
            if verbose:
                print(f" - {user}: found in cache")
            continue
        user_status = get_lock_status(user)
        if user_status is not False and "locked" in user_status:
            if cache_only:
                continue
            lock_event = get_lock_event(user)
            if lock_event is not False and "comment" in lock_event:
                locked_accounts.append(user)
                if check_lock_reason(lock_event["comment"]) is None:
                    print(
                        f" - {user}: locked, but for another reason ({lock_event['comment']})"
                    )
                    continue
                page_content = wiki.page_text(user)
                if page_content is not None:
                    modify_user_page(wiki, user, page_content)
                    edited_accounts.append(user)
        else:
            if verbose:
                print(f" - {user}: not locked")
            unlocked_accounts.append(user)

    print("\nDone.")
    print(f"Staff accounts locked: {len(locked_accounts)}")
    print(f"Staff accounts not locked: {len(unlocked_accounts) + len(cached_accounts)}")
    print(f"Staff accounts cached: {len(cached_accounts)}")
    print(f"Staff accounts excluded: {len(excluded_accounts)}")
    print(f"Staff account user pages edited: {len(edited_accounts)}")
    print(f"Total: {len(staff_accounts)}")

    if os.path.isfile(cache_file) is False:
        print("\nCreating cache file...")
        unlocked_json = json.dumps(unlocked_accounts)
        unlocked_cache = open(cache_file, "w")
        unlocked_cache.write(unlocked_json)
        unlocked_cache.close()
        print("Unlocked accounts cached.")
