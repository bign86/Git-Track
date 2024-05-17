#!/usr/bin/env python
"""Converts an old version's database to the recent format.

The database of the rc-1 did not have a priority field. This script
just adds this to all issues."""

import pickle

ISSUE_FILE = '.issues'

if __name__ == "__main__":
    with open(ISSUE_FILE, 'rb') as issues:
        DB = pickle.load(issues)
        for issue in DB.values():
            if not hasattr(issue, 'priority'):
                issue.priority = 3
            if not hasattr(issue, 'tags'):
                issue.tags = []
            if not hasattr(issue, 'parent'):
                issue.parent = 0
            else:
                issue.parent = 0 if issue.parent is None else int(issue.parent)
            if not hasattr(issue, 'children'):
                issue.children = set()
            else:
                issue.children = sorted(set(issue.children))
            if not hasattr(issue, 'is_open'):
                issue.is_open = True if issue.status == 'open' else False
    with open(ISSUE_FILE, 'wb') as issues:
        pickle.dump(DB, issues, -1)
        
