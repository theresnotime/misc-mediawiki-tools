import re

userRegex = re.compile(r"\/.*")
commentRegex = re.compile(
    r"no longer (wokrs?|works?|employed)?.*?(WMF|Wikimedia|here|for (us|the)|at foundation)|laid(-| )?off|contract ended|off(-| )?board(ing)?",
    re.IGNORECASE,
)
fsRegex = re.compile(r"{{former( |_)staff}}\n", re.IGNORECASE)
categoryRegex = re.compile(
    r"\[\[Category:Wikimedia( |_)Foundation( |_)staff\]\]", re.IGNORECASE
)
userinfoRegex = re.compile(r"{{user( |_)info", re.IGNORECASE)
cleanupRegex = re.compile(r"\| ?former ?= ?yes\n", re.IGNORECASE)
wiki_domain_regex = re.compile(r"https://(?P<wiki_domain>.*?)/wiki", re.IGNORECASE)
