import wmf_staff_accounts
from types import SimpleNamespace

if __name__ == "__main__":
    # Create a fake args object to pass to wmf_staff_accounts.main()
    args = SimpleNamespace(yes=True, regen_cache=False, dry=True, diff=False)

    # List of projects
    projects = [
        "meta.wikimedia.org",
        "en.wikipedia.org",
        "de.wikipedia.org",
        "commons.wikimedia.org",
        "simple.wikipedia.org",
        "es.wikipedia.org",
        "en.wikinews.org",
        "en.wikiquote.org",
        "en.wikiversity.org",
        "en.wikivoyage.org",
    ]

    # Run for each project
    for project in projects:
        print(f"[mass_cache] Starting cache for {project}...")
        wmf_staff_accounts.main(args, project, True, True, "./cache")
        print(f"[mass_cache] Done cache for {project}.\n\n")
