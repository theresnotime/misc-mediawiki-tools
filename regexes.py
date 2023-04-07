import re

userRegex = re.compile(r"\/.*")
commentRegex = re.compile(r"no longer works? .*?(WMF|Wikimedia|here)", re.IGNORECASE)
fsRegex = re.compile(r"{{former( |_)staff}}\n", re.IGNORECASE)
categoryRegex = re.compile(
    r"\[\[Category:Wikimedia( |_)Foundation( |_)staff\]\]", re.IGNORECASE
)
userinfoRegex = re.compile(r"{{user( |_)info", re.IGNORECASE)
cleanupRegex = re.compile(r"\| ?former ?= ?yes\n", re.IGNORECASE)
