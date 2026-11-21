#!/usr/bin/env python3
"""
What may appear on the panAtlas docs site, in one place. Adapted from the GaiaKeep docs filter
(GaiaKeep/docs scripts/public_filter.py), which carries the owner decision of 2026-10-06: facility and
institution identifiers are never published.

scrub(text)  rewrites internal detail (workstation paths, cluster and web hosts, accounts, storage paths,
             private addresses) into neutral words. Apply it when copying a document from the private repo.
check(root)  fails on anything that must never be published (credentials, identifiers, private documents) and on
             internal detail that survived. deploy.sh and the pre-push hook run it.
deny(root)   fails on any word that contains a name on a private list. The list is held here only as SHA-256 digests
             of the lower-case names, so this public script names none of them. deploy.sh and the pre-push hook run it
             over the whole repository.

    python3 scripts/public_filter.py check [docs]
    python3 scripts/public_filter.py deny [.]
"""
import hashlib
import re
import sys
from pathlib import Path

# (pattern, replacement): internal detail rewritten on the way into the site
SCRUB = [
    (re.compile(r"/Users/[^\s)`'\"\]]+"), "<local workspace path>"),
    (re.compile(r"/home/vbu\d+[^\s)`'\"\]]*"), "<cluster home>"),
    (re.compile(r"/project/ibi-staff[^\s)`'\"\]]*"), "<cluster project storage>"),
    (re.compile(r"\bdgx\.ai\.uky\.edu\b"), "the HPC cluster"),
    (re.compile(r"\bcaai\.ai\.uky\.edu\b"), "the web host"),
    (re.compile(r"\bslogin-\d+\b"), "a login node"),
    (re.compile(r"\bvbu\d{3}(_[a-z0-9]+)?\b"), "<cluster account>"),
    (re.compile(r"\b(10|100\.(6[4-9]|[7-9]\d|1[01]\d|12[0-7]))\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"), "<private address>"),
    (re.compile(r"\b192\.168\.\d{1,3}\.\d{1,3}\b"), "<private address>"),
    (re.compile(r"\b172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}\b"), "<private address>"),
    (re.compile(r"\bthe DGX cluster\b"), "the HPC cluster"),
    (re.compile(r"\bDGX cluster\b"), "HPC cluster"),
    (re.compile(r"\bThe DGX\b"), "The HPC cluster"),
    (re.compile(r"\bthe DGX\b"), "the HPC cluster"),
    (re.compile(r"\bdgx-(\d+)\b"), r"cluster node \1"),
    (re.compile(r"\bDGX\b"), "HPC"),
    # the web host and the global controller host
    (re.compile(r"\bthe caai (host|server|agent|node)\b", re.IGNORECASE), r"the web host \1"),
    (re.compile(r"\bcaai\b", re.IGNORECASE), "the web host"),
    (re.compile(r"\bparanib\b", re.IGNORECASE), "the global controller host"),
    # partner sites and institutional identifiers
    (re.compile(r"\buky\b"), "site-a"),
    (re.compile(r"\buofl\b", re.IGNORECASE), "site-b"),
    (re.compile(r"\blouisville\b", re.IGNORECASE), "site-b"),
]

# never publishable: the check fails outright
FORBIDDEN = [
    (re.compile(r"\bghp_[A-Za-z0-9]{30,}"), "GitHub token"),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{30,}"), "GitHub token"),
    (re.compile(r"\bgho_[A-Za-z0-9]{30,}"), "GitHub OAuth token"),
    (re.compile(r"\bpat_[A-Za-z0-9]{40}\b"), "panAtlas federation token"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private key"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AWS key id"),
    (re.compile(r"\b(SVC|DSG|DSR|DSA|\w*_service_key|discovery_secret_\w+)\s*=\s*['\"]?(?!\$\{|<|CHANGE-ME)[0-9A-Za-z+/_-]{12,}"),
     "service key or join secret"),
    (re.compile(r"\b\d{4}-\d{4}-\d{4}-\d{3}[0-9X]\b"), "ORCID iD (none are published; gates are described, not listed)"),
    (re.compile(r"\bUniversity of Kentucky\b", re.IGNORECASE), "institution name"),
    (re.compile(r"\bUniversity of Louisville\b", re.IGNORECASE), "institution name"),
    (re.compile(r"\bKentucky\b"), "state/institution identifier"),
    (re.compile(r"\b[\w.-]*uky\.edu\b"), "institutional hostname"),
    (re.compile(r"\b[\w.-]*louisville\.edu\b"), "institutional hostname"),
    (re.compile(r"\bCAAI\b"), "facility name"),
    (re.compile(r"\bKCDI\b"), "facility name"),
    (re.compile(r"^\s*(?:>\s*)?\*\*(?:PRIVATE\b|Private\.\*\*)"), "a document marked private"),
    (re.compile(r"ncbi\.key|api[_-]?key\s*[=:]\s*['\"]?[0-9a-f]{20,}", re.IGNORECASE), "API key or key file"),
]

# Named only so the check reports them; they need an owner decision, not an automatic rewrite, because they are
# exact dataset identifiers (slugs/URNs) that also carry an institution's initials.
REVIEW = [
    (re.compile(r"\bUK-ADRC\b|\bukadrc\b", re.IGNORECASE), "dataset name carries an institution's initials (UK-ADRC)"),
    (re.compile(r"heartlens-uk\b|ct-heartlens-uk", re.IGNORECASE), "dataset slug carries an institution's initials"),
]

PRIVATE = re.compile(r"^\s*(?:>\s*)?\*\*(?:PRIVATE\b|Private\.\*\*)|never goes to the public docs site")


def private(text: str) -> bool:
    return any(PRIVATE.search(line) for line in text.splitlines()[:15])


def scrub(text: str) -> str:
    for rx, rep in SCRUB:
        text = rx.sub(rep, text)
    return text


# The public documentation names neither the old framework nor its successor, nor their parts (owner, 2026-11-21).
# The words it must not contain are kept only as SHA-256 digests of their lower-case form, so this public script
# names none of them. Any word that holds one (a compound identifier included) is refused.
DENY_SHA256 = {
    '0d674b294ed4ffe655ccb0854edf8de1bd00cb8ba851ac0bb91d089294069964',
    '165a0bcdbd95b70e52afb155f2f5430a100c7664066b766d85dcfbf657448d96',
    '348d6394aba35ca9f566acfe2fd53858d0271dc4de37c8a5c87a63d4b512be7e',
    '4425af4a256dd8b7f72563e87467b7f8e66de13b911e230065c0382f81eb8b4c',
    '70cc3f5141676bc2442767a668f2a528fab5845b621ac3cde0725da0a840f11c',
    '7e3873975beb1bbc29a2ad32b32abfa86c167171aa282062f95befb217b0c334',
    '83f11be5ee6a5cf41a19c344be3755d8919e9fa3ce1a0d3670d689a661529cf7',
    'ba28b074d56946088423b0a0935719911ac3fddd37d069116eae76cd246a96cf',
    'c649ae712de60722742f6346fa1e827fe83d230efd322b461d59943b37fcabbf',
    'cd5d154f9061ee927ee2f3ad9eb5c04450fad1a0bee94a3f7b3d93dd615b198e',
    'e0c1bf97b7eb4405fbd0f40e6cf10fea93799c76a5c3cdf7875553ec6de86668',
}
_DENY_LENS = (4, 5, 6, 7, 8, 9, 10, 11, 12)
_WORD = re.compile(r"[A-Za-z][A-Za-z0-9]*")


def denied(line: str) -> list:
    """The words of a line that contain a denied name (by digest)."""
    hits = []
    for w in _WORD.findall(line):
        lw = w.lower()
        if any(hashlib.sha256(lw[i:i + n].encode()).hexdigest() in DENY_SHA256
               for n in _DENY_LENS for i in range(0, max(0, len(lw) - n) + 1)):
            hits.append(w)
    return hits


def deny_check(root: Path) -> int:
    """Every text file under root (the whole repository: pages, scripts, configuration), except build output."""
    bad = 0
    skip = {".git", ".venv", "site", "__pycache__"}
    for p in sorted(root.rglob("*")):
        if not p.is_file() or skip.intersection(p.relative_to(root).parts):
            continue
        if p.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif", ".ico", ".woff", ".woff2", ".ttf", ".pdf"):
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        for n, line in enumerate(text.splitlines(), 1):
            for w in denied(line):
                print(f"FORBIDDEN a private name ({w}): {p}:{n}")
                bad += 1
    return bad


def check(root: Path, strict_review: bool = False) -> int:
    bad = 0
    review = 0
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.suffix not in (".md", ".yml", ".yaml", ".html", ".txt", ".json", ".py", ".js", ".css", ".svg"):
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        for n, line in enumerate(text.splitlines(), 1):
            for rx, what in FORBIDDEN:
                if rx.search(line):
                    print(f"FORBIDDEN {what}: {p}:{n}")
                    bad += 1
            for rx, _ in SCRUB:
                m = rx.search(line)
                if m:
                    print(f"internal detail not scrubbed: {p}:{n}: {m.group(0)}")
                    bad += 1
            for rx, what in REVIEW:
                if rx.search(line):
                    print(f"REVIEW {what}: {p}:{n}")
                    review += 1
    if review:
        print(f"public_filter: {review} line(s) need an owner decision before the site is public (REVIEW)")
    return bad + (review if strict_review else 0)


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "deny":
        root = Path(sys.argv[2] if len(sys.argv) > 2 else ".")
        n = deny_check(root)
        print(f"public_filter: {n} private name(s) in {root}")
        sys.exit(1 if n else 0)
    if len(sys.argv) >= 2 and sys.argv[1] == "check":
        args = [a for a in sys.argv[2:] if not a.startswith("--")]
        root = Path(args[0] if args else "docs")
        n = check(root, strict_review="--public" in sys.argv)
        print(f"public_filter: {n} problem(s) in {root}")
        sys.exit(1 if n else 0)
    print(__doc__)
