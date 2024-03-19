# Show a tree in the command line

BRANCH = '├'
PIPE = '|'
END = '└'
DASH = '─'

LEN_STR = 100


def draw_tree(db: dict, issue_id: int = None) -> None:
    if issue_id:
        base_items = [db[issue_id]]
    else:
        base_items = set(
            issue for issue in db.values()
            if issue.parent == 0 and issue.status == 'open'
        )
        base_items = sorted(base_items, key=lambda v: v.priority)

    length = len(base_items)
    str_length = LEN_STR - 9
    for n, item in enumerate(base_items, 1):
        msg = item.msg.split('\n')[0][:str_length]
        status = '\033[32m\u2588\033[0m' \
            if item.status == 'open' \
            else '\033[31m\u2588\033[0m'

        if n == length:
            print(f' {END} {item.my_id:>03d} {status} {msg}')
            _draw_children(db, item.children, prfx='   ')
        else:
            print(f' {BRANCH} {item.my_id:>03d} {status} {msg}')
            _draw_children(db, item.children, prfx=f' {PIPE} ')
    print()


def _draw_children(db: dict, children: list, prfx: str) -> None:
    items = [db[my_id] for my_id in children]
    items = sorted(items, key=lambda v: v.priority)

    length = len(items)
    str_length = LEN_STR - 9 - len(prfx)
    for n, child in enumerate(items, 1):
        msg = child.msg.split('\n')[0][:str_length]
        status = '\033[32m\u2588\033[0m' \
            if child.status == 'open' \
            else '\033[31m\u2588\033[0m'

        if n == length:
            print(f'{prfx} {END} {child.my_id:>03d} {status} {msg}')
            _draw_children(db, child.children, prfx=prfx + '   ')
        else:
            print(f'{prfx} {BRANCH} {child.my_id:>03d} {status} {msg}')
            _draw_children(db, child.children, prfx=prfx + f' {PIPE} ')
