import argparse
import config
import defaults
import random
import re
import requests
import sys
import time
from datetime import datetime
from pwiki.wiki import Wiki
from termcolor import cprint

wiki = Wiki("en.wikipedia.org", "TNTBot", config.TNT_BOT_PASS)
# TODO: Remember that non-capturing regex exists, silly (:
removal_regex = re.compile(
    r"<!-- THE FOLLOWING( TWO)? CATEGOR.*?(!<-- \*\*\* -->)? ?<!-- Template:",
    re.IGNORECASE,
)
edit_summary = "Removing [[CAT:UAA]] from indefinitely blocked editor ([[Wikipedia:Bots/Requests for approval/TNTBot 6|BRFA]])"
stats = {}
stats["checked_subcats"] = 0
stats["checked_users"] = 0
stats["start_time"] = round(time.time())


def get_subcats() -> list[str]:
    """Get the subcategories of the UAA category"""
    return wiki.category_members(
        "Category:Wikipedia usernames with possible policy issues", ["Category"]
    )


def get_category_members(category: str) -> list[str]:
    """Get the members of a category"""
    return wiki.category_members(category, ["User talk"])


def log_data(
    data: str,
    filename: str,
    also_print: bool = False,
    dont_write_to_file: bool = False,
    colour_print=None,
    underline: bool = False,
) -> None:
    """Log data to a file/terminal"""
    with open(filename, "a+") as f:
        dt_string = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        content = f"{dt_string}: {data}"
        if not dont_write_to_file:
            f.write(content + "\n")
        if also_print:
            if underline:
                cprint(content, colour_print, attrs=["underline"])
            else:
                cprint(content, colour_print)


def log_to_wiki(data: str) -> None:
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


def remove_page_from_category(page: str) -> None:
    """Remove a page from the UAA category"""
    content = wiki.page_text(page)
    new_content = removal_regex.sub("<!-- Template:", content)
    if not defaults.DRY:
        log_data(f"Editing {page}...", "cleanup_cat_uaa-debug.log", also_print=True)
        wiki.edit(
            title=page,
            text=new_content,
            summary=edit_summary,
            minor=True,
        )
    else:
        log_data(
            f"Dry run, not editing {page}", "cleanup_cat_uaa-debug.log", also_print=True
        )
    time.sleep(1)


def get_last_edit(expected_page: str):
    bot_contribs = wiki.contribs("User:TNTBot", ns=["User talk"])
    return bot_contribs[0]


def get_page_last_edit(page: str):
    last_edit = wiki.revisions(page)[0]
    if last_edit.user == "TNTBot":
        return last_edit
    else:
        return False


def check_for_block(user: str) -> bool:
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


def make_log_message(user: str, subcat: str, revid) -> str:
    """Make a log message for a user"""
    dt_string = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    username = user.replace("User talk:", "")
    template_str = "{{noping|" + username + "}}"
    if revid:
        return f"{dt_string}: Removed ([[Special:Diff/{revid}|diff]]) {template_str} from [[:{subcat}]] -- ~~~~"
    else:
        return f"{dt_string}: Removed {template_str} from [[:{subcat}]] -- ~~~~"


def check_category(subcat: str) -> None:
    """Check a UAA subcategory for indefinitely blocked users"""
    stats["checked_subcats"] += 1
    wiki.purge(subcat)
    subcat_members = get_category_members(subcat)
    subcat_size = len(subcat_members)
    log_data(
        f"Checking category {subcat} ({subcat_size})...",
        "cleanup_cat_uaa-debug.log",
        also_print=True,
        colour_print="blue",
        underline=True,
    )
    time.sleep(0.3)
    random.shuffle(subcat_members)
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
                colour_print="green",
            )
            remove_page_from_category(user)
            if not defaults.DRY:
                revision = get_page_last_edit(user)
                if revision:
                    revision_id = revision.revid
                else:
                    revision_id = False
                log_to_wiki(make_log_message(user, subcat, revision_id))
                log_data(
                    f"Removed {user} from {subcat}.",
                    "cleanup_cat_uaa-debug.log",
                    also_print=True,
                    colour_print="green",
                )
                time.sleep(1)
                if defaults.SUPERVISED:
                    cprint(
                        "1 edit made, and supervised testing is enabled. Exiting.",
                        "blue",
                    )
                    sys.exit()
        else:
            log_data(
                f"{user} is not yet blocked indefinitely.",
                "cleanup_cat_uaa-debug.log",
                also_print=True,
                colour_print="yellow",
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
    parser.add_argument("--shuffle", help="Shuffle subcategories", action="store_true")
    parser.add_argument("--dry", help="Don't make any edits", action="store_true")
    parser.add_argument(
        "--supervised",
        help="Supervised testing (make 1 edit and exit)",
        action="store_true",
    )
    args = parser.parse_args()
    defaults.DRY = args.dry
    defaults.SUPERVISED = args.supervised

    print("Starting UAA cleanup...")

    if defaults.DRY:
        cprint("Dry run enabled. No edits will be made.", "blue")
        time.sleep(1)

    if defaults.SUPERVISED:
        cprint("Supervised testing enabled. Only one edit will be made.", "blue")
        time.sleep(1)

    if args.cat:
        cprint(f"Only checking {args.cat}", "blue")
        check_category(args.cat)
    else:
        uaa_subcats = get_subcats()
        if args.shuffle:
            cprint("Shuffling subcategories...", "blue")
            random.shuffle(uaa_subcats)
        for subcat in uaa_subcats:
            check_category(subcat)

    stats["end_time"] = round(time.time())
    stats["elapsed_time"] = round(stats["end_time"] - stats["start_time"])
    print(f"Elapsed time: ~{stats['elapsed_time']} seconds.")
    print(f"Checked {stats['checked_subcats']} UAA subcategories.")
    print(f"Checked {stats['checked_users']} users.")
