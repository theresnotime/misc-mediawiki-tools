import common_utils
import wmf_staff_accounts
from types import SimpleNamespace


def manually_login(project) -> bool:
    print(f"[mass_cache] Logging in to {project}...")
    print("TODO")
    return False


def do_cache(args, project) -> bool:
    return wmf_staff_accounts.main(args, project, True, True, "./cache")


def get_args(category):
    # Create a fake args object to pass to wmf_staff_accounts.main()
    args = SimpleNamespace(
        yes=True,
        regen_cache=False,
        dry=True,
        diff=False,
        cache_only=True,
        category=category,
    )
    return args


if __name__ == "__main__":
    projects = common_utils.get_projects()
    print(f"[mass_cache] Got {len(projects)} projects to cache...")

    # Run for each project
    for project in projects:
        title, wiki_domain = common_utils.parse_project(projects, project)
        if wiki_domain is None or title is None:
            print(f"[mass_cache] Skipping {project} due to missing data.\n\n")
            continue

        print(f"[mass_cache] Starting cache for {wiki_domain}...")
        try:
            print(get_args(title))
            result = do_cache(get_args(title), wiki_domain)
        except Exception as e:
            print(f"[mass_cache] Error: {e}")
            print("[mass_cache] Continuing to next project...\n\n")
            continue
        if result:
            print(f"[mass_cache] Done caching for {wiki_domain}.\n\n")
        else:
            # Try a manual login then try again
            manually_login(wiki_domain)
            result = do_cache(get_args(title), wiki_domain)
            if result:
                print(f"[mass_cache] Done caching for {wiki_domain}.\n\n")
            else:
                print(f"[mass_cache] Cache failed for {wiki_domain}.\n\n")
