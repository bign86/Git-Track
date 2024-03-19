# The central pieces of code...

from tabulate import tabulate
from git import Repo
from git.exc import InvalidGitRepositoryError
from shutil import which
import datetime
import os
import pickle
import time
import subprocess
import sys

ISSUE_FILE = '.issues'
_EDITORS = ('nano', 'vim', 'vi', 'emacs')
_HEADERS = ("id", "Date", "Status", "Pr", "Tags", "Comment")


def catch_id_err(func):
    """ Decorator to catch errors from wrong ids. """

    def _safe(self, my_id, *args, **kwargs):
        """ Id-safe version of ... """
        try:
            func(self, my_id, *args, **kwargs)
        except KeyError:
            print(f"{my_id}: no such issue!")
        except ValueError:  # comes from int(...)
            print("No or invalid id given!")

    return _safe


def safe_tmp_textfile(func):
    """ Make sure that the __issue__.msg file does not exist and if so,
        move it to a backup. Delete it after function call.
    """

    def _safe(self, *args, **kwargs):
        """ Cleanup the file __issue__.msg before and after call. """
        if os.path.exists("__issue__.msg"):
            os.rename("__issue__.msg", "__issue__.msg~")
        func(self, *args, **kwargs)
        if os.path.exists("__issue__.msg"):
            os.remove("__issue__.msg")

    return _safe


class IssueDB(object):
    """ 'Database' managing the issues. """

    def __init__(self):
        try:
            Repo('.')
            try:
                _ = Repo('.').head.commit.hexsha
            except ValueError:
                print("Git repository .git has no head commit!")
                sys.exit()
        except InvalidGitRepositoryError:
            print("No git repository fond in .git!")
            sys.exit()

        self.issue_db = {}
        self.max_id = 0
        if os.path.exists(ISSUE_FILE):
            with open(ISSUE_FILE, 'rb') as issues:
                self.issue_db = pickle.load(issues)
                self.max_id = max(self.issue_db)

        # Set editor
        editor = str(os.getenv('EDITOR'))
        if editor == 'None':
            for ed in _EDITORS:
                if which(ed) is not None:
                    self.editor = str(ed)
                    break
        else:
            self.editor = str(editor.split(':')[0])

        if self.editor is None:
            raise RuntimeError('No shell editor found!')

    def __str__(self) -> str:
        """ Prints all active issues. """
        data = [
            issue.to_list()
            for issue in sorted(self.issue_db.values())[::-1]
            if issue.is_open
        ]
        return tabulate(data, headers=_HEADERS)

    #
    # Top-level commands
    #

    @safe_tmp_textfile
    def add(self) -> None:
        """ Add an issue. """
        # Set priority and tags
        prio = max(0, min(5, int(input('Priority [0-5]: '))))
        tag = input('Give a tag: ')

        subprocess.call([self.editor, '__issue__.msg'])
        if os.path.exists('__issue__.msg'):
            message = open('__issue__.msg', 'r')
            msg = message.read()
            sha = self._get_head_sha()

            self.max_id += 1
            self.issue_db[self.max_id] = Issue(self.max_id, sha, prio, tag, msg)

            self._repickle()
            message.close()
            print('Added issue\n', self.issue_db[self.max_id])
        else:
            print('Abort: Empty message!')

    @catch_id_err
    def close(self, issue_id: int, wontfix: bool) -> None:
        """ Close a specific issue. """
        issue = self.issue_db[issue_id]

        if any(self.issue_db[child].is_open for child in issue.children):
            print('This issue cannot be closed as there are open children. Close dependent issues first')

        else:
            status = 'wontfix' if wontfix else 'close'
            issue.closedsha = self._get_head_sha()
            issue.status = status
            issue.is_open = False
            self._repickle()

    @catch_id_err
    def edit(self, issue_id: int, ns) -> None:
        """ Edit an issue. """
        if ns.prio is not None:
            self._set_prio(issue_id, ns.prio[0])
        elif ns.add_tag is not None:
            self._edit_tag(issue_id, '+', ns.add_tag[0])
        elif ns.rm_tag is not None:
            self._edit_tag(issue_id, '-', ns.rm_tag[0])
        elif ns.attach is not None:
            self._edit_parent(issue_id, ns.attach[0])
        elif ns.detach:
            self._edit_parent(issue_id, 0)
        else:
            self._edit_msg(issue_id)

    @catch_id_err
    def remove(self, issue_id: int) -> None:
        """ Remove a specific issue. """
        issue = self.issue_db[issue_id]
        for child in issue.children:
            self.issue_db[child].parent = issue.parent

        del self.issue_db[issue_id]
        self._repickle()

    def search(self, ns) -> None:
        """ Search in the DB for a given string. """
        filtered_ids = []
        if ns.string is not None:
            string = ns.string.lower()
            for _id, issue in self.issue_db.items():
                if string in issue.msg.lower():
                    filtered_ids.append(_id)
        else:
            filtered_ids = list(self.issue_db.keys())

        to_show = []
        if ns.tag is not None:
            tag = ns.tag[0]
            for _ in range(len(filtered_ids)):
                _id = filtered_ids.pop()
                issue = self.issue_db[_id]
                if tag in issue.tags:
                    to_show.append(issue.to_list())
        else:
            while filtered_ids:
                _id = filtered_ids.pop()
                to_show.append(self.issue_db[_id].to_list())

        print(tabulate(to_show, headers=_HEADERS))

    @catch_id_err
    def show(self, issue_id: int, show_all: bool, show_closed: bool) -> None:
        """ To show issues info and lists. """
        if show_all:
            print(self._show_all())
        elif show_closed:
            print(self._show_closed())
        elif issue_id is not None:
            self._info(issue_id)
        else:
            print(self)

    #
    # Internal methods
    #

    def _show_all(self) -> str:
        """ Prints also closed issues. """
        data = [
            issue.to_list()
            for issue in sorted(self.issue_db.values())[::-1]
        ]
        return tabulate(data, headers=_HEADERS)

    def _show_closed(self) -> str:
        """ Prints all closed issues. """
        data = [
            issue.to_list()
            for issue in sorted(self.issue_db.values())[::-1]
            if not issue.is_open
        ]
        return tabulate(data, headers=_HEADERS)

    def _repickle(self) -> None:
        """ Rewrite database. """
        with open(ISSUE_FILE, 'wb') as issues:
            pickle.dump(self.issue_db, issues, -1)

    @staticmethod
    def _get_head_sha() -> str:
        """ Get head commit sha. """
        return Repo('.').head.commit.hexsha

    def _set_prio(self, issue_id, prio: int) -> None:
        try:
            self.issue_db[issue_id].priority = int(prio)
            self._repickle()
        except ValueError:
            print("Priority must be integer!")

    def _info(self, issue_id) -> None:
        """ Get info on a specific issue. """
        self.issue_db[issue_id].more_info()

    @catch_id_err
    def re_add(self, issue_id) -> None:
        """ Reset the sha to the latest commit. """
        self.issue_db[issue_id].commitsha = self._get_head_sha()
        self._repickle()

    @safe_tmp_textfile
    def _edit_msg(self, issue_id) -> None:
        """ Change the message of an existing issue. """
        with open('__issue__.msg', 'w') as message:
            message.write(self.issue_db[issue_id].msg)

        subprocess.call([self.editor, '__issue__.msg'])
        message = open('__issue__.msg', 'r')
        msg = message.read()
        self.issue_db[issue_id].msg = msg
        self._repickle()
        message.close()

    def _edit_tag(self, issue_id, op: str, tag: str) -> None:
        """ Change the message of an existing issue. """
        if op == '+':
            self.issue_db[issue_id] \
                .tags \
                .append(tag)
        elif op == '-':
            self.issue_db[issue_id] \
                .tags \
                .remove(tag)
        self._repickle()

    @catch_id_err
    def _edit_parent(self, issue_id, parent: int):
        """ Attach or detach an issue to/from a parent. """
        issue = self.issue_db[issue_id]

        if issue.parent == parent:
            return

        elif issue.parent == 0:
            if parent not in self.issue_db:
                print(f"{parent}: no such issue!")
            else:
                self.issue_db[parent].children.add(issue_id)
                issue.parent = parent
                self._repickle()

        elif parent == 0:
            self.issue_db[issue.parent].children.remove(issue_id)
            issue.parent = 0
            self._repickle()

        else:
            if parent not in self.issue_db:
                print(f"{parent}: no such issue!")
            else:
                self.issue_db[parent].children.add(issue_id)
                self.issue_db[issue.parent].children.remove(issue_id)
                issue.parent = parent
                self._repickle()


class Issue(object):
    """ Issue object. """

    _MAX_MSG_L = 80

    def __init__(self, my_id, commit_sha, priority, tags, msg):
        self.my_id = my_id
        self.commit_sha = commit_sha
        self.closed_sha = ""
        self.msg = msg
        self.issued = datetime.datetime.now()
        self.status = 'open'
        self.is_open = True
        self.priority = priority
        self.tags = [tags]
        self.parent = 0
        self.children = set()

    def __str__(self) -> str:
        return "\t".join(self.to_list())

    def to_list(self) -> list:
        msg = self.msg.split("\n")[0]  # get the first line
        return [
            f"{self.my_id:>03d}",
            self.issued.strftime("%y %b %d"),
            self.status,
            str(self.priority),
            ' '.join(self.tags),
            len(msg) > self._MAX_MSG_L and msg[:(self._MAX_MSG_L - 3)] + "..." or msg
        ]

    def __gt__(self, other) -> bool:
        return self.my_id > other.my_id \
            if self.priority == other.priority \
            else self.priority > other.priority

    def __lt__(self, other) -> bool:
        return self.my_id < other.my_id \
            if self.priority == other.priority \
            else self.priority < other.priority

    def get_commit(self, sha=""):
        """ Get the corresponding commit object. """
        repo = Repo('.')
        return repo.commit(sha or self.commit_sha)

    def more_info(self) -> None:
        """ Print detailed information. """
        print(f"Issue {self.my_id:3d}")
        print("-" * 70)
        print(
            f"Status: {self.status}\nDate:   {self.issued.strftime('%a %b %d %H:%M %Y')}\n"
            f"Tags: {' '.join(self.tags)}\n{self.msg}\n"
            f"Parent: {self.parent}\nChildren: {','.join(self.children)}"
        )
        if self.closed_sha:
            print("-" * 70)
            print("Closed with:")
            self._print_info(self.get_commit(self.closed_sha))
        print("-" * 70)
        print("Opened:")
        self._print_info(self.get_commit())

    @staticmethod
    def _print_info(commit) -> None:
        """ Print info on commit. """
        print(
            f"commit  {commit.hexsha}\n"
            f"Author: {str(commit.author)}\n"
            f"Date:   {time.asctime(time.gmtime(commit.committed_date))}\n\n"
            f"{commit.message}"
        )
