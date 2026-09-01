"""Check your 03 lab: is the site changed, verified, committed, and pushed?

Run it on your copy of the lab, work/03/lab, from the root of the course repo:
    python3 work/03/lab/check.py        (Windows: python work/03/lab/check.py)
It finds its own folder, so python3 check.py from inside the copy works too.

Six checks, one PASS or FAIL line each, then a summary line; the exit code is
0 only when all six pass.  They verify that the site files are here
(index.html, style.css, .nojekyll), that index.html links style.css by a
relative path, that the placeholder line in index.html is gone (this one stays
FAIL until you replace it), that verification/ holds a real screenshot (a PNG
or JPEG image; a fetch.txt beside it is welcome but does not count), that this
folder is a git repository of its own with at least
two commits, and that a remote named origin exists, this branch tracks it, and
nothing is left to commit or push.
It changes nothing: no file is written and the network is never used, so it
cannot see your pull request or the live page; the screenshot is your proof.
It needs only Python 3 and git.  Claude Code runs it when you say "/lab check".
"""

import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE_FILES = ("index.html", "style.css", ".nojekyll")
PLACEHOLDER = "TODO: replace this sentence"  # the line in index.html that the lab replaces
RELATIVE_LINK = re.compile(r"""href\s*=\s*["']style\.css["']""")
ABSOLUTE_LINK = re.compile(r"""href\s*=\s*["']/style\.css["']""")
VERIFY_DIR = "verification"
IMAGE_STARTS = {".png": b"\x89PNG\r\n\x1a\n", ".jpg": b"\xff\xd8\xff", ".jpeg": b"\xff\xd8\xff"}
MIN_IMAGE_BYTES = 4096  # a real screenshot is far bigger than a placeholder image
PUSH = "commit and push to your GitHub repo"


def git(*args):
    """Run one git command in this folder and return (exit code, its output)."""
    try:
        run = subprocess.run(["git", *args], cwd=HERE, capture_output=True, text=True)
    except FileNotFoundError:
        return 127, "install git first (see setup.md in the course repo)"
    return run.returncode, (run.stdout + run.stderr).strip()


def read_text(name):
    """The text of a file in this folder, or None when it is missing."""
    path = os.path.join(HERE, name)
    if not os.path.isfile(path):
        return None
    with open(path, "rb") as handle:
        return handle.read().decode("utf-8", errors="replace")


def own_repo():
    """Why this folder is not a git repository of its own, or None when it is."""
    code, output = git("rev-parse", "--is-inside-work-tree")
    if code != 0:
        return output if code == 127 else "run 'git init -b main' here in work/03/lab, then make your first commit"
    code, top = git("rev-parse", "--show-toplevel")
    if code == 0 and os.path.normcase(os.path.realpath(top)) != os.path.normcase(os.path.realpath(HERE)):
        return (
            f"this folder is not a git repository of its own yet (git found the course repo at {top}): "
            f"run 'git init -b main' here in work/03/lab, then make your first commit"
        )


def check_files():
    missing = [name for name in SITE_FILES if not os.path.isfile(os.path.join(HERE, name))]
    if ".nojekyll" in missing:
        return "create an empty file named .nojekyll in this folder (it is hidden, so the copy may have skipped it)"
    if missing:
        return f"put {' and '.join(missing)} back in this folder (copy from class/03-git-verify-deploy/lab/starter/)"


def check_relative_link():
    html = read_text("index.html")
    if html is None:
        return "fix the check above first"
    if RELATIVE_LINK.search(html):
        return None
    if ABSOLUTE_LINK.search(html):
        return 'change the stylesheet link back to href="style.css" (no leading slash; /style.css breaks on a project-site URL)'
    return 'keep the line <link rel="stylesheet" href="style.css"> in index.html'


def check_placeholder():
    html = read_text("index.html")
    if html is None:
        return "fix the checks above first"
    if PLACEHOLDER in html:
        return "open index.html, find the line marked TODO, and replace it with a sentence of your own"


def check_verification():
    """Only a real image counts; a fetch.txt beside it is extra evidence, not the screenshot."""
    folder = os.path.join(HERE, VERIFY_DIR)
    ask = f"save a screenshot of the live page, address bar visible, as {VERIFY_DIR}/screenshot.png"
    if not os.path.isdir(folder):
        return f"make a folder named {VERIFY_DIR} here, then " + ask
    rejected = []
    for name in sorted(os.listdir(folder)):
        path = os.path.join(folder, name)
        extension = os.path.splitext(name)[1].lower()
        if not os.path.isfile(path) or extension not in IMAGE_STARTS:
            continue
        with open(path, "rb") as handle:
            head = handle.read(8)
        if head.startswith(IMAGE_STARTS[extension]) and os.path.getsize(path) >= MIN_IMAGE_BYTES:
            return None
        rejected.append(name)
    if rejected:
        return f"{VERIFY_DIR}/{rejected[0]} is too small or not a real image: " + ask
    return ask


def check_commits():
    problem = own_repo()
    if problem:
        return problem
    code, count = git("rev-list", "--count", "HEAD")
    if code != 0:
        return 'make your first commit here (git add . then git commit -m "Start the 03 lab")'
    if int(count) < 2:
        return (
            'make a commit with your change (git add . then git commit -m "Replace the placeholder line"); '
            f"this folder has {count} commit and the lab needs at least 2, the starter and then your change"
        )


def check_pushed():
    if own_repo():
        return "fix the check above first"
    if git("remote", "get-url", "origin")[0] != 0:
        return PUSH + (
            " (origin is git's name for the copy on GitHub; create it with "
            "gh repo create <name> --public --source=. --remote=origin --push, or ask Claude Code to)"
        )
    if git("rev-parse", "--abbrev-ref", "@{u}")[0] != 0:
        return PUSH + " (this branch is not tracking origin yet: git push -u origin HEAD)"
    code, unpushed = git("log", "@{u}..HEAD", "--oneline")
    if code != 0:
        return PUSH + f" (git could not compare this branch with origin: {unpushed.splitlines()[-1] if unpushed else 'no details'})"
    if unpushed:
        count = len(unpushed.splitlines())
        return PUSH + f" ({count} commit{'s' if count != 1 else ''} not pushed yet)"
    if git("status", "--porcelain", "--", "index.html", VERIFY_DIR)[1]:
        return PUSH + f" (index.html or {VERIFY_DIR}/ has changes that are not committed yet)"


CHECKS = [
    ("the site files are here (index.html, style.css, .nojekyll)", check_files),
    ("index.html links style.css by a relative path", check_relative_link),
    ("the placeholder line in index.html is replaced", check_placeholder),
    ("verification/ holds a real screenshot image", check_verification),
    ("this folder is its own git repository with at least two commits", check_commits),
    ("everything is pushed to origin on GitHub", check_pushed),
]


def main():
    passed = 0
    for what, check in CHECKS:
        try:
            problem = check()
        except Exception as error:
            problem = f"something unexpected happened ({type(error).__name__}: {error})"
        print(f"FAIL {what}: {problem}" if problem else f"PASS {what}")
        passed += 0 if problem else 1
    print("All checks passed." if passed == len(CHECKS) else f"{passed} of {len(CHECKS)} checks passed.")
    return 0 if passed == len(CHECKS) else 1


if __name__ == "__main__":
    sys.exit(main())
