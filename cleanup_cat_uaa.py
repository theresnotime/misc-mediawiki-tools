import argparse
import config
import defaults
import re
import requests
import time
from datetime import datetime
from pwiki.wiki import Wiki

wiki = Wiki("en.wikipedia.org", "TNTBot", config.TNT_BOT_PASS)
removal_regex = re.compile(
    r"<!-- THE FOLLOWING TWO CATEGORIES .*?<!-- \*\*\* -->", re.IGNORECASE
)
edit_summary = "Removing [[CAT:UAA]] from indefinitely blocked editor ([[Wikipedia:Bots/Requests for approval/TNTBot 6|BRFA]])"
stats = {}
stats["checked_subcats"] = 0
stats["checked_users"] = 0
stats["start_time"] = time.time()


def get_subcats():
    """Get the subcategories of the UAA category"""
    return wiki.category_members(
        "Category:Wikipedia usernames with possible policy issues", ["Category"]
    )


def get_category_members(category):
    """Get the members of a category"""
    return wiki.category_members(category, ["User talk"])


def log_data(data, filename, also_print=False, dont_write_to_file=False):
    """Log data to a file/terminal"""
    with open(filename, "a+") as f:
        dt_string = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        content = f"{dt_string}: {data}"
        if not dont_write_to_file:
            f.write(content + "\n")
        if also_print:
            print(content)


def log_to_wiki(data):
    """Log data to a subpage"""
    log_page = "User:TNTBot/Logs/UAA Cleanup"
    content = wiki.page_text(log_page)
    content += f"\n* {data}"
    if not defaults.DRY:
        wiki.edit(
            title=log_page,
            text=content,
            summary="Logging UAA cleanup",
            minor=True,
        )
    else:
        print(f"Dry run, not logging {data}")


def remove_page_from_category(page):
    """Remove a page from the UAA category"""
    content = wiki.page_text(page)
    new_content = removal_regex.sub("", content)
    if not defaults.DRY:
        log_data(f"Editing {page}...", "cleanup_cat_uaa-debug.log", also_print=True)
        wiki.edit(
            title=page,
            text=new_content,
            summary="Removing user from UAA category",
            minor=True,
        )
    else:
        log_data(
            f"Dry run, not editing {page}", "cleanup_cat_uaa-debug.log", also_print=True
        )
    time.sleep(1)


def check_for_block(user):
    """Check if a user is blocked indefinitely"""
    user = user.replace("User talk:", "")
    response = requests.get(
        f"https://en.wikipedia.org/w/api.php?action=query&format=json&list=blocks&formatversion=2&bkusers={user}&bkshow=!temp",
        headers=defaults.HEADERS,
    )
    json = response.json()
    if "error" in json:
        print(f"Error: {json['error']['info']}")
        return False
    if len(json["query"]["blocks"]) == 0:
        return False
    else:
        return True


def check_category(subcat):
    """Check a UAA subcategory for indefinitely blocked users"""
    stats["checked_subcats"] += 1
    wiki.purge(subcat)
    subcat_members = get_category_members(subcat)
    subcat_size = len(subcat_members)
    log_data(
        f"Checking {subcat} ({subcat_size})...",
        "cleanup_cat_uaa-debug.log",
        also_print=True,
    )
    for user in subcat_members:
        stats["checked_users"] += 1
        log_data(
            f"Checking {user} for an indef block...",
            "cleanup_cat_uaa-debug.log",
            also_print=True,
        )
        user_blocked = check_for_block(user)
        if user_blocked:
            log_data(
                f"{user} is blocked indefinitely.",
                "cleanup_cat_uaa-debug.log",
                also_print=True,
            )
            remove_page_from_category(user)
            log_data(
                f"Removed {user} from {subcat}.",
                "cleanup_cat_uaa-debug.log",
                also_print=True,
            )
        else:
            log_data(
                f"{user} is not yet blocked indefinitely.",
                "cleanup_cat_uaa-debug.log",
                also_print=True,
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="cleanup_cat_uaa.py",
        description="Cleanup the UAA category",
    )
    parser.add_argument(
        "-c",
        "--cat",
        help="Run on one specific category",
    )
    parser.add_argument("--dry", help="Don't make any edits", action="store_true")
    args = parser.parse_args()
    defaults.DRY = args.dry

    if defaults.DRY:
        print("Dry run enabled. No edits will be made.")

    if args.cat:
        check_category(args.cat)
    else:
        uaa_subcats = get_subcats()
        for subcat in uaa_subcats:
            check_category(subcat)

    stats["end_time"] = time.time()
    stats["elapsed_time"] = round(stats["end_time"] - stats["start_time"])
    print(f"Elapsed time: ~{stats['elapsed_time']} seconds.")
    print(f"Checked {stats['checked_subcats']} UAA subcategories.")
    print(f"Checked {stats['checked_users']} users.")
