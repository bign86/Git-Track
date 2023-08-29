#!/usr/bin/env python

import argparse
from issue_db.issue_db import IssueDB


if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog='Git-Track')
    subparsers = parser.add_subparsers(help='sub-commands help')
    parser.set_defaults(func='')

    # create the parser for the "add" command
    parser_add = subparsers.add_parser('add', help='add help')
    parser_add.set_defaults(func='add')

    # create the parser for the "close" command
    parser_close = subparsers.add_parser('close', help='close help')
    parser_close.set_defaults(func='close')
    parser_close.add_argument('--wontfix', action='store_true',
                              help='no fix will happen', default=False)
    parser_close.add_argument('id', type=int, help='id issue')

    # create the parser for the "edit" command
    parser_edit = subparsers.add_parser('edit', help='edit help')
    parser_edit.set_defaults(func='edit')
    parser_edit.add_argument('id', type=int, help='id issue')
    parser_edit.add_argument('--prio', nargs=1, type=int, help='change priority')
    parser_edit.add_argument('--add-tag', nargs=1, type=str, help='remove a tag')
    parser_edit.add_argument('--rm-tag', nargs=1, type=str, help='add a tag')

    # create the parser for the "rm" command
    parser_rm = subparsers.add_parser('remove', help='remove help')
    parser_rm.set_defaults(func='remove')
    parser_rm.add_argument('id', type=int, help='id issue')

    # create the parser for the "rm" command
    parser_search = subparsers.add_parser('search', help='search help')
    parser_search.set_defaults(func='search')
    parser_search.add_argument('string', nargs='?', type=str, help='string to search for')
    parser_search.add_argument('--tag', nargs=1, type=str, help='search for this tag')

    # create the parser for the "show" command
    parser_show = subparsers.add_parser('show', help='show help')
    parser_show.set_defaults(func='show')
    parser_show.add_argument('--all', action='store_true',
                             help='to show all issues', default=False)
    parser_show.add_argument('--info', nargs=1, type=int,
                             help='show detailed info on id')

    args = parser.parse_known_args()
    ns = args[0]

    ISSUES = IssueDB()

    if ns.func == 'show':
        issue_id = None if ns.info is None else ns.info[0]
        ISSUES.show(issue_id, ns.all)
    elif ns.func == 'add':
        ISSUES.add()
    elif ns.func == 'remove':
        ISSUES.remove(ns.id)
    elif ns.func == 'close':
        ISSUES.close(ns.id, ns.wontfix)
    elif ns.func == 'edit':
        ISSUES.edit(ns.id, ns)
    elif ns.func == 'search':
        ISSUES.search(ns)

