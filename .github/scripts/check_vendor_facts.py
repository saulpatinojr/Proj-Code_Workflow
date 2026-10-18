#!/usr/bin/env python3
"""Check that every fact in docs/client-facts.json is still stated on its official page.

Fetches each page once, reduces it to plain text, and looks for the fact's phrase. A missing phrase or an
unreachable page means the vendor changed or moved something, so docs/client-locations.md needs re-verifying.

Usage: python .github/scripts/check_vendor_facts.py [--facts docs/client-facts.json] [--markdown OUT]
Exit 1 when any fact could not be confirmed.
"""
from __future__ import annotations

import argparse
import gzip
import html
import json
import re
import sys
import urllib.error
import urllib.request
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def normalize(text: str) -> str:
    text = re.sub(r"(?is)<(script|style|noscript)\b.*?</\1>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = html.unescape(text)
    text = text.replace("\\", "/").replace("`", "").replace("*", "").replace("​", "")
    text = " ".join(text.split()).lower()
    # Pages often split code spans into separate elements, which renders "~/.copilot/agents/" as "~/ .copilot/ agents/".
    return re.sub(r"\s*/\s*", "/", text)


def fetch(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; code-workflow-facts/1.0)",
                                                   "Accept": "text/html,text/markdown,text/plain;q=0.9,*/*;q=0.8",
                                                   "Accept-Encoding": "gzip, deflate"})
    with urllib.request.urlopen(request, timeout=60) as response:
        body = response.read()
        # Some CDNs compress even when not asked; urllib never decompresses, so do it here.
        encoding = (response.headers.get("Content-Encoding") or "").lower()
        if encoding == "gzip" or body[:2] == b"\x1f\x8b":
            body = gzip.decompress(body)
        elif encoding == "deflate":
            body = zlib.decompress(body)
        return body.decode(response.headers.get_content_charset() or "utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--facts", default=str(ROOT / "docs" / "client-facts.json"))
    parser.add_argument("--markdown", help="write a Markdown report of unconfirmed facts to this file")
    args = parser.parse_args()
    facts = json.loads(Path(args.facts).read_text(encoding="utf-8"))["facts"]
    pages: dict[str, str | Exception] = {}
    for url in sorted({f["url"] for f in facts}):
        try:
            pages[url] = normalize(fetch(url))
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            pages[url] = exc
    problems = []
    for fact in facts:
        page = pages[fact["url"]]
        if isinstance(page, Exception):
            status = f"page unreachable ({page})"
        elif normalize(fact["phrase"]) in page:
            status = "confirmed"
        else:
            status = "phrase not found"
        print(f"{status:<18} {fact['id']:<32} {fact['url']}")
        if status != "confirmed":
            problems.append((fact, status))
    print(f"{len(facts) - len(problems)} of {len(facts)} facts confirmed")
    if args.markdown:
        lines = ["These facts from `docs/client-facts.json` could not be confirmed on their official pages. "
                 "The vendor may have changed or moved them; re-verify the matching rows of `docs/client-locations.md`.", "",
                 "| Client | Fact | Result | Page | Expected phrase |", "|---|---|---|---|---|"]
        lines += [f"| {f['client']} | {f['fact']} | {s} | {f['url']} | `{f['phrase']}` |" for f, s in problems]
        Path(args.markdown).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
