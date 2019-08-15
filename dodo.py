import glob

from doit.action import CmdAction

PACKAGE = "ehforwarderbot"
DEFAULT_BUMP_MODE = "beta"
# major, minor, patch, alpha, beta, dev, post
DOIT_CONFIG = {
    "default_tasks": ["msgfmt"]
}


def task_sphinx_html():
    return {
        "actions": ["sphinx-build -b html ./docs docs/_build"]
    }


def task_gettext():
    pot = "./{package}/locale/{package}.pot".format(package=PACKAGE)
    sources = glob.glob("./{package}/**/*.py".format(package=PACKAGE), recursive=True)
    sources = [i for i in sources if "__version__.py" not in i]
    command = "xgettext --add-comments=TRANSLATORS -o " + pot + " " + " ".join(sources)
    sources += glob.glob("./docs/**/*.rst", recursive=True)
    targets = [pot] + glob.glob("./docs/_build/locale/**/*.pot", recursive=True)
    return {
        "actions": [
            command,
            "sphinx-build -b gettext ./docs docs/_build/locale/"
        ],
        "targets": targets,
        "file_dep": sources
    }


def task_msgfmt():
    sources = glob.glob("./{package}/**/*.po".format(package=PACKAGE), recursive=True)
    dests = [i[:-3] + ".mo" for i in sources]
    actions = [["msgfmt", sources[i], "-o", dests[i]] for i in range(len(sources))]
    return {
        "actions": actions,
        "targets": dests,
        "file_dep": sources,
        "task_dep": ['crowdin', 'crowdin_pull']
    }


def task_crowdin():
    sources = glob.glob("./{package}/**/*.pot".format(package=PACKAGE), recursive=True)
    return {
        "actions": ["crowdin upload sources"],
        "file_dep": sources,
        "task_dep": ["gettext"],
        "verbosity": 1
    }


def task_crowdin_pull():
    return {
        "actions": ["crowdin download"],
        "verbosity": 1,
        "task_dep": ["crowdin"]
    }


def task_commit_lang_file():
    return {
        "actions": [
            ["git", "add", "*.po"],
            ["git", "commit", "-m", "Sync localization files from Crowdin"]
        ],
        "task_dep": ["crowdin", "crowdin_pull"]
    }


def task_bump_version():
    def gen_bump_version(mode=DEFAULT_BUMP_MODE):
        return './bump.py ' + mode

    return {
        "actions": [CmdAction(gen_bump_version)],
        "params": [
            {
                "name": "Version bump mode",
                "short": "b",
                "long": "bump",
                "default": DEFAULT_BUMP_MODE,
                "help": "{major}.{minor}.{patch}{(a|b)}{.post}{.dev}",
                "choices": [
                    ("major", "Bump a major version"),
                    ("minor", "Bump a minor version"),
                    ("patch", "Bump a patch version"),
                    ("alpha", "Bump to the next alpha version"),
                    ("alpha", "Bump to the next beta version"),
                    ("post", "Bump to the next post version"),
                    ("dev", "Bump a dev version (for commit only)")
                ]
            }
        ],
        "task_dep": ["test", "commit_lang_file"]
    }


def task_mypy():
    actions = ["mypy -p {}".format(PACKAGE)]
    return {
        "actions": actions,
        "verbosity": 1
    }


def task_test():
    sources = glob.glob("./{package}/**/*.py".format(package=PACKAGE), recursive=True)
    return {
        "actions": [
            "coverage run --source ./{} -m pytest".format(PACKAGE),
            "coverage report"
        ],
        "file_dep": sources,
        "verbosity": 2
    }


def task_build():
    return {
        "actions": [
            "python setup.py sdist bdist_wheel"
        ],
        "task_dep": ["test", "msgfmt", "bump_version"]
    }


def task_publish():
    def get_twine_command():
        __version__ = __import__("{}.__version__".format(PACKAGE)).__version__
        if 'dev' in __version__:
            raise ValueError(f"Cannot publish dev version ({__version__}).")
        binary = glob.glob("./dist/*{}*".format(__version__), recursive=True)
        return ' '.join(["twine", "upload"] + binary)
    return {
        "actions": [CmdAction(get_twine_command)],
        "task_dep": ["build"]
    }
