import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import check, finish, py, read, suite  # noqa: E402

readme = read("README.md")


def section(title: str) -> str:
    i = readme.find(title)
    if i < 0:
        return ""
    j = readme.find("\n## ", i + 1)
    return readme[i : j if j > 0 else len(readme)]


UNTOUCHED = {
    "## Install": "## Install\n\n```sh\npip install -e .\n```\n\nOr run it straight from a checkout with `python -m tally`.\n",
    "## Development": "## Development\n\n```sh\npython3 -m unittest discover -s tests\n```\n",
    "## License": "## License\n\nMIT\n",
}
for title, text in UNTOUCHED.items():
    check(section(title).rstrip() == text.rstrip(), f"README section {title!r} left alone")

usage = section("## Usage")
check(bool(usage), "README still has a Usage section")
check("--category" not in readme, "the stale --category flag is gone")

# Ask the real parser what exists.
code = r"""
import argparse, json
from tally.cli import build_parser
p = build_parser()
out = {}
for a in p._actions:
    if isinstance(a, argparse._SubParsersAction):
        for name, sp in a.choices.items():
            out[name] = [o.option_strings for o in sp._actions if o.option_strings and '-h' not in o.option_strings]
print(json.dumps(out))
"""
r = py(code)
commands = json.loads(r.stdout) if r.returncode == 0 else {}
check(bool(commands), "could introspect the CLI parser")
for name, options in commands.items():
    check(re.search(rf"\btally\s+{name}\b", usage) is not None, f"Usage documents the `{name}` subcommand")
    for opts in options:
        check(any(o in usage for o in opts), f"Usage documents `{name} {'/'.join(opts)}`")

check(suite().returncode == 0, "the repo's own test suite passes")
finish()
