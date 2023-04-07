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

wiki = Wiki("meta.wikimedia.org", "TNTBot", config.TNT_BOT_BADIMAGE_PASS)
cacheFile = "unlocked_accounts.json"
CATEGORY = "Category:Wikimedia Foundation staff"
HEADERS = {"User-Agent": "TNTBot (https://meta.wikimedia.org/wiki/User:TNTBot)"}
DRY = True
VIEW_DIFF = True
DELAY = 15
SUMMARY = "([[User:TNTBot#Marking_former_WMF_staff_accounts|automated]]) Marking user as former staff — many thanks, and best wishes for the future."


def get_staff_accounts():
    wiki.purge(CATEGORY)
    time.sleep(3)
    return wiki.category_members(CATEGORY, ["User"])


def validate_user(user):
    return re.search(regexes.userRegex, user)


def get_staff_status(user):
    response = requests.get(
        f"https://meta.wikimedia.org/w/api.php?action=query&format=json&meta=globaluserinfo&formatversion=2&guiuser={user}",
        headers=HEADERS,
    )
    json = response.json()
    if "error" in json:
        print(f"Error: {json['error']['info']}")
        return False
    return json["query"]["globaluserinfo"]


def get_lock_event(user):
    response = requests.get(
        f"https://meta.wikimedia.org/w/api.php?action=query&format=json&list=logevents&formatversion=2&letype=globalauth&letitle={user}%40global&lelimit=1",
        headers=HEADERS,
    )
    json = response.json()
    if "error" in json:
        print(f"Error: {json['error']['info']}")
        return False
    return json["query"]["logevents"][0]


def check_lock_reason(reason):
    return re.search(regexes.commentRegex, reason)


def check_cache(user):
    if os.path.isfile(cacheFile):
        unlocked_cache = open(cacheFile, "r")
        unlocked_accounts = json.loads(unlocked_cache.read())
        unlocked_cache.close()
        if user in unlocked_accounts:
            return True
    return False


def modification_date(filename):
    t = os.path.getmtime(filename)
    return datetime.datetime.fromtimestamp(t)


def rm_formerstaff(page_content):
    return regexes.fsRegex.sub("", page_content)


def rm_category(page_content):
    return regexes.categoryRegex.sub("", page_content)


def add_formerparam(page_content):
    return regexes.userinfoRegex.sub("{{user info\n| former = true", page_content)


def cleanup_params(page_content):
    return regexes.cleanupRegex.sub("", page_content)


def modify_user_page(user, page_content):
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

    print(f"Sleeping for {DELAY} seconds...")
    time.sleep(DELAY)
    return new_content


if __name__ == "__main__":
    if DRY:
        print("Dry run mode enabled. No edits will be made.")
    print(f"Purging {CATEGORY} and getting staff accounts...")
    staff_accounts = get_staff_accounts()
    unlocked_accounts = []
    locked_accounts = []
    edited_accounts = []
    cached_accounts = []

    print(f"Got {len(staff_accounts)} staff accounts. Checking cache file...")

    if os.path.isfile(cacheFile):
        print(f"Cache file last modified: {modification_date(cacheFile)}")
        if datetime.datetime.now() - modification_date(cacheFile) > datetime.timedelta(
            hours=12
        ):
            print("Cache file is older than 12 hours, deleting...")
            os.remove(cacheFile)
        else:
            print("Cache file is less than 12 hours old — OK to use.")
    else:
        print("No cache file found — will create one.")

    print("")

    for user in staff_accounts:
        if validate_user(user) is not None:
            print(f" - {user}: not a user page")
            continue
        if check_cache(user) is True:
            cached_accounts.append(user)
            continue
        user_status = get_staff_status(user)
        if user_status is not False and "locked" in user_status:
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
                    modify_user_page(user, page_content)
                    edited_accounts.append(user)
        else:
            unlocked_accounts.append(user)

    print("\nDone.")
    print(f"Staff accounts locked: {len(locked_accounts)}")
    print(f"Staff accounts not locked: {len(unlocked_accounts) + len(cached_accounts)}")
    print(f"Staff accounts cached: {len(cached_accounts)}")
    print(f"Staff account user pages edited: {len(edited_accounts)}")
    print(f"Total: {len(staff_accounts)}")

    if os.path.isfile(cacheFile) is False:
        print("\nCreating cache file...")
        unlocked_json = json.dumps(unlocked_accounts)
        unlocked_cache = open(cacheFile, "w")
        unlocked_cache.write(unlocked_json)
        unlocked_cache.close()
        print("Unlocked accounts cached.")
