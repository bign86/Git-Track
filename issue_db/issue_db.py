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
            if issue.status == 'open'
        ]
        return tabulate(data, headers=("id", "Date", "Status", "Pr", "Tags", "Comment"))

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
        status = 'wontfix' if wontfix else 'close'
        self.issue_db[issue_id].closedsha = self._get_head_sha()
        self.issue_db[issue_id].status = status
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
        else:
            self._edit_msg(issue_id)

    @catch_id_err
    def remove(self, issue_id: int) -> None:
        """ Remove a specific issue. """
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

        print(
            tabulate(
                to_show,
                headers=("id", "Date", "Status", "Pr", "Tags", "Comment")
            )
        )

    @catch_id_err
    def show(self, issue_id: int, show_all: bool) -> None:
        """ To show issues info and lists. """
        if show_all:
            print(self._show_all())
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
        return tabulate(data, headers=("id", "Date", "Status", "Pr", "Tags", "Comment"))

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


class Issue(object):
    """ Issue object. """

    def __init__(self, my_id, commit_sha, priority, tags, msg):
        self.my_id = my_id
        self.commit_sha = commit_sha
        self.closed_sha = ""
        self.msg = msg
        self.issued = datetime.datetime.now()
        self.status = 'open'
        self.priority = priority
        self.tags = [tags]

    def __str__(self) -> str:
        return "\t".join(self.to_list())

    def to_list(self) -> list:
        msg = self.msg.split("\n")[0]  # get the first line
        return [
            "%03i" % self.my_id,
            self.issued.strftime("%b %d"),
            # self.commit_sha[:8],
            self.status,
            str(self.priority),
            ' '.join(self.tags),
            len(msg) > 50 and msg[:47] + "..." or msg
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
            f"Tags: {' '.join(self.tags)}\n{self.msg}"
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
