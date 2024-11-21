import wmf_staff_accounts
from types import SimpleNamespace

if __name__ == "__main__":
    # Create a fake args object to pass to wmf_staff_accounts.main()
    args = SimpleNamespace(
        yes=True, regen_cache=False, dry=True, diff=False, cache_only=True
    )

    # List of projects
    projects = [
        "www.mediawiki.org",
        "commons.wikimedia.org",
        "meta.wikimedia.org",
        # wikipedias
        "test.wikipedia.org",
        "test2.wikipedia.org",
        "simple.wikipedia.org",
        "en.wikipedia.org",
        "de.wikipedia.org",
        "es.wikipedia.org",
        # others
        "en.wikinews.org",
        "en.wikiquote.org",
        "en.wikiversity.org",
        "en.wikivoyage.org",
        "www.wikidata.org",
    ]

    # Run for each project
    for project in projects:
        print(f"[mass_cache] Starting cache for {project}...")
        wmf_staff_accounts.main(args, project, True, True, "./cache")
        print(f"[mass_cache] Done cache for {project}.\n\n")
