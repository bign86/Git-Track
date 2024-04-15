#!/usr/bin/env python

import argparse
from issue_db import *
from issue_db import VERSION


if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog='Git-Track')
    subparsers = parser.add_subparsers(help='sub-commands help')
    parser.set_defaults(func='')
    parser.add_argument('--version', action='store_true', default=False)

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
    parser_edit.add_argument('--attach', nargs=1, type=int, help='add a parent')
    parser_edit.add_argument('--detach', action='store_true', help='remove the parent')

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
    parser_show.add_argument('--closed', action='store_true',
                             help='to show closed issues', default=False)
    parser_show.add_argument('--info', nargs=1, type=int,
                             help='show detailed info on id')

    # create the parser for the "tree" command
    parser_show = subparsers.add_parser('tree', help='tree help')
    parser_show.set_defaults(func='tree')
    parser_show.add_argument('id', nargs='?', type=int, help='id issue')

    args = parser.parse_known_args()
    ns = args[0]

    ISSUES = IssueDB()

    if ns.func == 'show':
        issue_id = None if ns.info is None else ns.info[0]
        ISSUES.show(issue_id, ns.all, ns.closed)
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
    elif ns.func == 'tree':
        draw_tree(ISSUES.issue_db, ns.id)
    elif ns.version:
        print(f'Git-Track: {VERSION}')
    else:
        parser.print_help()

