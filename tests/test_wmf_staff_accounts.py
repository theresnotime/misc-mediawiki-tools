import defaults
import wmf_staff_accounts


def test_cleanup_params():
    assert (
        wmf_staff_accounts.cleanup_params("{{user info\n| former = yes\n")
        == "{{user info\n"
    )
    assert (
        wmf_staff_accounts.cleanup_params("{{user info\n|former=yes\n")
        == "{{user info\n"
    )
    assert (
        wmf_staff_accounts.cleanup_params("{{user info\n| former = true\n")
        == "{{user info\n| former = true\n"
    )
    assert (
        wmf_staff_accounts.cleanup_params("{{user info\n|former=true\n")
        == "{{user info\n|former=true\n"
    )


def test_add_formerparam():
    assert (
        wmf_staff_accounts.add_formerparam("{{user info")
        == "{{user info\n| former = true"
    )


def test_rm_formerstaff():
    assert (
        wmf_staff_accounts.rm_formerstaff("{{former staff}}\n{{user info")
        == "{{user info"
    )


def test_complete_userinfo_modification():
    """Test the complete modification of a user page."""
    with open("tests/test_data/example_userinfo_pre.txt", "r") as file:
        example_userinfo_pre = file.read()
    with open("tests/test_data/example_userinfo_post.txt", "r") as file:
        example_userinfo_post = file.read()

    defaults.DRY = True
    wiki = object()
    assert (
        wmf_staff_accounts.modify_user_page(wiki, "TNTBot", example_userinfo_pre)
        == example_userinfo_post
    )
