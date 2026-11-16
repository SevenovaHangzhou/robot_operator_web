"""The pages run under style-src 'self': style attributes in markup are blocked by the browser."""

from pathlib import Path
import re

import pytest

from integ_operator_web.server import security_headers

WEB = Path(__file__).resolve().parents[1] / "web"
# A style attribute written into HTML or into markup strings that scripts insert.
STYLE_ATTRIBUTE = re.compile(r"""\sstyle\s*=\s*["'$]""")
SOURCES = sorted(
    path
    for pattern in ("**/*.html", "**/*.js", "**/*.mjs")
    for path in WEB.glob(pattern)
    if "vendor" not in path.parts
)


def test_the_pages_forbid_inline_styles():
    assert "style-src 'self';" in security_headers(())["Content-Security-Policy"]


@pytest.mark.parametrize("path", SOURCES, ids=lambda path: str(path.relative_to(WEB)))
def test_no_style_attributes_in_page_markup(path):
    lines = [
        f"{number}: {line.strip()}"
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1)
        if STYLE_ATTRIBUTE.search(line)
    ]
    assert lines == []
