#!/usr/bin/env python

import sys
from issue_db.issue_db import IssueDB


COMMANDS = ("show", "add", "info", "rm", "close", "showall", "re-add",
            "edit", "prio")


def print_help():
    print(
        f"usage: {sys.argv[0]} command\n"
        f"commands:\n"
        f"     show       Show all open issues.\n"
        f"     showall    Show all issues.\n"
        f"     info id    More information on issue with id.\n"
        f"     add        Add issue.\n"
        f"     re-add     Set the issue sha to current HEAD's.\n"
        f"                Useful if you did a git commit --amend.\n"
        f"     edit       Edit issue message corresponding to id.\n"
        f"     close id   Close issue with id.\n"
        f"     rm id      Remove issue with id.\n"
        f"     prio id p  Set priority of id to integer value p.",
        end='\n\n'
    )


if __name__ == "__main__":
    ISSUES = IssueDB()
    ARGS = sys.argv
    ARGS += ["", ""]
    CMD, OPT = ARGS[1:3]

    if CMD not in COMMANDS:
        print_help()
    else:
        if CMD == 'show':
            print(ISSUES)
        elif CMD == 'add':
            ISSUES.add_issue()
        elif CMD == 'info':
            ISSUES.info(OPT)
        elif CMD == 'rm':
            ISSUES.remove(OPT)
        elif CMD == 'close':
            ISSUES.close(OPT)
        elif CMD == 'showall':
            print(ISSUES.show_all())
        elif CMD == 're-add':
            ISSUES.re_add(OPT)
        elif CMD == 'edit':
            ISSUES.edit(OPT)
        elif CMD == 'prio':
            ISSUES.set_prio(OPT, ARGS[3])
