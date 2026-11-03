#!/usr/bin/env python3
"""Deterministic, offline integrity checks for Kaiwen Live documentation."""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping
from urllib.parse import unquote, urlsplit


DOC_PATHS = (
    "AGENTS.md",
    "README.md",
    "README.upstream-20261030.md",
    "docs/AGENT_INTEGRATION.md",
    "docs/ARCHITECTURE.md",
    "docs/DESIGN_AND_UX.md",
)

# SHA-256(source path + NUL + label + NUL + URL) -> occurrence count.
# This is the Live-only D8 label+URL multiset. It avoids embedding private
# document bodies; CI never fetches any target.
APPROVED_PINNED_DIGESTS = Counter({
    "28e3965435d13cfb397df2499c96aa272a3816f8a0836c83c7597663746898bb": 1,
    "e55042f37224672e52c2336f9cb8210b19d8902179b31c44def602859366ad29": 2,
    "a0e1fe54fbb46c7a91522dc229beae0f6cd84595835630bb2a8a151a624abb00": 1,
    "178c0af27fc8312c2c698bd2dde21430b8cdda5f10795ae9e61eda0a4aa266df": 2,
    "77a2b31300fd2819a0ea3abe8b226f6727fcca0675a5b9af00b13d47bde63f6b": 2,
    "ed467c3ad95771f0e269e4fd94c293f67aecda59369c5074096885316c9b7e35": 2,
    "40ef147166bc6c48f1b4ddaf6444fd811081e847ac9ff140a3366f6dc52e8559": 2,
    "621bfd423b760a97786e63a77a789f0f142c9c91dc39877700d208ef5081c57b": 2,
    "6e38d2acbb36a1d43c168e5e11bdb1f9885a728598acc0747dbd57d514df9432": 1,
    "556fb4f4cca05db12793f3feb739b157f69ad2444e446c1ca802be1297768f79": 2,
    "69ce7a68b95b4a3fa22ca60f65c0d4b38081a7fc1b0224fd4ed58b1ae9024fac": 1,
    "501d992e9064d52b3364a1dc223d16ac2e7d54fd315af1b57926edeb280b00f3": 1,
    "9a6e7c9117119ca81d1601ad9210ee4e76047cfec6ed7b68480212af4a2c7b77": 1,
    "afd7655919202368030a72c2441f9ec2a57f8b9c863778383fd3d8634de7a5c6": 1,
    "ce1f138a931c9cc9a20818ae93b9ca74470353b829648e67cba1d5b0676d06f3": 1,
    "e21dd98ea6d459d6b175631a58cd771485ccfceaaedc38fc4cd547f3ea0efde2": 1,
    "4076d79295f0e83d5f8d16fe97f5142463e2119ba962c7271a16311dec1b9b6e": 3,
    "e9f23d5b028afe992f7a06226554ec3d135d949f0ac3fb448201be832a60c545": 1,
    "361216823695f473e0bcff540aae3a6b9cf649f68530a0091c4f5727b7e6d90f": 2,
    "7d0c7826c484406dc76f3fdeadc0b217526da8e29f09bb7313146c41204e56f0": 1,
    "3fdc924c81e3151bbf6ed7e759fc47d46a6ad181cede9a9486d3459df272b953": 1,
    "0a721e4a5925ec9a75a4aec2793a6788d395b28752d0f6a197aeea557c36d4f5": 1,
    "f5cf26a6f9e507d715534fde889684e2c3064bd9f4352eeba8b0a89b4fa1a609": 1,
    "8da6f99febded4be001d84fa0377bc4fb9b979cb69554f0eed46ba164648cc75": 1,
    "9cd47124de04de3b6a7ee7ced30ee7740a41aaafa17e2c124f190965d3cf3289": 2,
    "cede8e3dd608a62124c0b603147e0449825a7ae339ccb059eac3c7e341c61ff1": 2,
    "4bc8e5f8b70b4cbd7c64fd49b3462b1d63975e67a3a32d03098d2abda3b9bf66": 1,
    "4ee8f334ac28ef0d91d11eec751f3b9c6b3fad64b043bd6790d9cde630d27a7a": 2,
    "50bfa4cfca95c64f1e15acfe3c8338940ade1acbf3ea38a65351efb5fbae0b44": 1,
    "e3f28557388b7d94c7b4939210540527f08ab004ad90e1ba153597b892d54434": 2,
    "8d32a028d35cdf148c25206986347013c74b581f077bdededb3273f9f2f99dc9": 1,
    "85f74603804256bdf752aeed5d4416d7e334d861b904258964c401751769d60f": 1,
    "48ee1faf7f17dc51e745678bc1a6b76e7393d2259df349f9f77955f525388f17": 1,
    "985ae9202772564b59af83b009faefe3ea259b3566737e5518a57479c7fea0cb": 1,
    "f9f58757d8af0b604395a7774673d54cb8a35e4fe549a937ae968354e3edb8e8": 2,
    "5d5045c1d8b06174bdece4c618b63b1a0b50836f248b86ea268cfc0c6faf98f3": 1,
    "7eb695360d889a0a5ac806a8b184a83c27ceaa8a4710f4842434d89cd2687b79": 2,
    "a9ee6c45e1ea8cf5dd60f1d4a602132077a49039b1d77ccf67825308ceb20672": 3,
    "d58c48d3ee2bf276fab972e7dd280da57220207b652a107ef45f7f273bb16087": 3,
    "dd12f5cc1402bf0df017b99fd65ba999dbf08ba16f22e9811cc375d0c74ea1b7": 2,
    "25484e3dfab9feb8979673b214c35584c83b02edbb4487666112d94005e44421": 1,
    "e3e895e43ab2ebf260a3659c7b01afeebe4d2305b60aaface690a317f938cafa": 1,
    "fecc53a35302182f6ed8b766c3177cd302604e1518b1e9603d691a602b6278ee": 1,
    "226320eb3809fa982d13045ccc5d4846e3359293b182068abfd5047d20e81aed": 2,
    "300b792d71a522f53893d19bce0cc072f8e63f849502fb73a74a0a4b5aade8c7": 1,
    "fc4e85dfb5579539f5fe455564ad000d2138b94f8b4f8af703140e22ef24c8bc": 3,
    "8f0e057ea2bfded98424b29abe46bc4226cb2cbb400e9b419b7a7b87320021ec": 2,
    "f1711fa5a9b133c0c7f405e444b16b991b03890be17798d7f231ba889fe6cf97": 3,
})

APPROVED_HARDBREAKS = {
    ("AGENTS.md", 3): "a35e241ed22fe54fdfc99a2821ca17a21cb52c746fa66dbf34aaa4074d196a5b",
    ("AGENTS.md", 4): "ad1d5ee9d27d7f71913d08e431892f95aec45cde34bf224e793e8133d44fd6ef",
    ("AGENTS.md", 5): "465d244f479281ad458134edd56c3ed89aabb5f4c78df952b95534c56e84d25b",
    ("AGENTS.md", 6): "597a4f6a9ef018f53c26a02797dcca287c74e19f41a0efe93e1a8f0a1f4fe8c5",
    ("AGENTS.md", 7): "6a19fb712a5670cee20aa816031fb2071ba232b425fb4d2b7290b7196d3b8a3b",
    ("docs/AGENT_INTEGRATION.md", 3): "5f37475ef49a055b0f28a2279b8ea33a2727e6f47447014ec5bb68f21d5b37ca",
    ("docs/AGENT_INTEGRATION.md", 4): "b018472aba6a58a628159d5c0f9454120fef13ca6fcb6f3f2ea2a96a3714eea8",
    ("docs/AGENT_INTEGRATION.md", 5): "5c19ffcdcc92e21e369df840631d846b93bc85bc5a9841e8c10eb0dce2ae0520",
    ("docs/AGENT_INTEGRATION.md", 6): "92d9471193edf328ffeab1a16be812102271c044311cfa652654ba9bbd19b37a",
    ("docs/AGENT_INTEGRATION.md", 7): "cdb76efafa6ae03570d21509e6f8f7cb73a251597e2ccf0f9ba3b1dfa05b3ec7",
    ("docs/ARCHITECTURE.md", 3): "903d0d37867d53ee41d32362e07fda04feda37289625dd29eaa190344250a65b",
    ("docs/ARCHITECTURE.md", 4): "0024147217786e53404528d73598712d627a883483b4af85748fd176b6dd0bc7",
    ("docs/ARCHITECTURE.md", 5): "4226ad5d55697e870b65e00e7356f7887572f3f41ebaa21edd420ad867f82bc9",
    ("docs/ARCHITECTURE.md", 6): "a50b6a33fa20ff832eac05cb7525154b278733d32c56965df7ae89148f8ffafd",
    ("docs/DESIGN_AND_UX.md", 3): "8d2f30384050c2bda5d5815cd806be3bf0da82e984b1b47029552de225e772dc",
    ("docs/DESIGN_AND_UX.md", 4): "0555e07fefc28511281ad3650fc6526a36157a1154175ddc6f02eb9f00decc7c",
    ("docs/DESIGN_AND_UX.md", 5): "1eb80e08180a77cf1b58e1f35943bbaf32e3140f4271995e2a2de0c2525bf604",
    ("docs/DESIGN_AND_UX.md", 6): "91795e2bb99445e9079717ae38670b2e299a138ae5b6092a2dd0f54ad2f6fe1b",
    ("docs/DESIGN_AND_UX.md", 7): "6bf61e9817b417ea497b50c158847dcaec7e8784937d8aa153409dab29731706",
    ("docs/DESIGN_AND_UX.md", 8): "c76635da3aae6c5f44a960000a6d279812ccb2566548a31498d5381847260b67",
}

EXPECTED_FILE_LINK_COUNTS = {
    "AGENTS.md": 17,
    "README.md": 15,
    "docs/AGENT_INTEGRATION.md": 13,
    "docs/ARCHITECTURE.md": 18,
    "docs/DESIGN_AND_UX.md": 12,
}
EXPECTED_REPO_LINK_COUNTS = {
    "kaiwen-ai": 28,
    "kaiwen-speech": 31,
    "kaiwen-corpus": 4,
    "kaiwen-forge": 12,
}
EXPECTED_VISIBILITY_COUNTS = {"PRIVATE": 63, "PUBLIC": 12}
REPO_VISIBILITY = {
    "kaiwen-ai": "PRIVATE",
    "kaiwen-speech": "PRIVATE",
    "kaiwen-corpus": "PRIVATE",
    "kaiwen-forge": "PUBLIC",
}
EXPECTED_PINNED_TARGETS = 12
HISTORICAL_CANONICAL_SHA256 = {
    "README.upstream-20261030.md": "5f4f07e39b4b4e5c6319f7e81ed72f756acb148d150c22988228a83c295ec366",
}

STALE_PHRASES = (
    "Henüz oluşturulacak.",
    "Sonraki belge; henüz yazılacak",
    "ileride yazılacak, henüz yok",
    "Henüz yazılmamış `docs/DESIGN_AND_UX.md`",
    "Sıradaki dosya `docs/ARCHITECTURE.md` olacaktır",
)
REQUIRED_CURRENT_PHRASES = (
    "`docs/ARCHITECTURE.md` mevcut mimari tasarım belgesidir",
    "HEDEF MİMARİ / UYGULAMA ŞARTNAMESİ — çalışan uygulama veya benchmark raporu değildir",
    "HEDEF / HENÜZ UYGULANMADI",
)

MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[([^\]]+)\]\(([^)\s]+)(?:\s+['\"][^'\"]*['\"])?\)")
FENCE_RE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
PINNED_URL_RE = re.compile(
    r"^https://github\.com/ImtheKaiwen/(kaiwen-ai|kaiwen-speech|kaiwen-corpus|kaiwen-forge)/"
    r"blob/([0-9a-f]{40})/(.+)$"
)
SECRET_PATTERNS = {
    "private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "github-token": re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    "aws-access-key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "signed-url": re.compile(
        r"https?://\S+[?&](?:X-Amz-Signature|sig|signature|token|access_token)="
        r"[A-Za-z0-9%._~-]{16,}", re.IGNORECASE
    ),
    "personal-path": re.compile(
        r"(?:[A-Za-z]:\\Users\\(?!REPLACE|<)[^\\\s]+|/(?:home|Users)/(?!REPLACE|<)[^/\s]+)"
    ),
}


@dataclass(frozen=True, order=True)
class Issue:
    path: str
    line: int
    rule: str
    message: str


def line_fingerprint(line: str) -> str:
    return hashlib.sha256(line.encode("utf-8")).hexdigest()


def link_fingerprint(source: str, label: str, url: str) -> str:
    return hashlib.sha256("\0".join((source, label, url)).encode("utf-8")).hexdigest()


def outside_fences(text: str) -> Iterable[tuple[int, str]]:
    opened: tuple[str, int] | None = None
    for number, line in enumerate(text.splitlines(), 1):
        match = FENCE_RE.match(line)
        if match:
            marker = match.group(1)
            if opened is None:
                opened = (marker[0], len(marker))
            elif marker[0] == opened[0] and len(marker) >= opened[1]:
                opened = None
            continue
        if opened is None:
            yield number, line


def extract_markdown_links(text: str) -> Iterable[tuple[int, str, str]]:
    for line_number, line in outside_fences(text):
        for match in MARKDOWN_LINK_RE.finditer(line):
            yield line_number, match.group(1), match.group(2)


def validate_document_bytes(
    path: str,
    data: bytes,
    approved_hardbreaks: Mapping[tuple[str, int], str] | None = None,
) -> tuple[str | None, list[Issue]]:
    approved_hardbreaks = approved_hardbreaks or {}
    issues: list[Issue] = []
    if data.startswith(b"\xef\xbb\xbf"):
        issues.append(Issue(path, 1, "utf8-bom", "UTF-8 BOM is not allowed"))
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return None, [Issue(path, 0, "utf8", "document is not strict UTF-8")]
    if "\r" in text:
        issues.append(Issue(path, 0, "line-ending", "CR/CRLF is not allowed"))
    if not data.endswith(b"\n") or data.endswith(b"\n\n"):
        issues.append(Issue(path, 0, "final-newline", "exactly one final newline is required"))

    lines = text.splitlines()
    seen: set[tuple[str, int]] = set()
    for number, line in enumerate(lines, 1):
        trailing = re.search(r"[ \t]+$", line)
        if not trailing:
            continue
        key = (path, number)
        if trailing.group(0) == "  " and approved_hardbreaks.get(key) == line_fingerprint(line):
            seen.add(key)
        else:
            issues.append(Issue(path, number, "trailing-whitespace", "unapproved trailing whitespace"))
    for key in sorted(k for k in approved_hardbreaks if k[0] == path and k not in seen):
        issues.append(Issue(path, key[1], "hardbreak-baseline", "approved hard-break is missing or changed"))

    opened: tuple[str, int, int] | None = None
    for number, line in enumerate(lines, 1):
        match = FENCE_RE.match(line)
        if not match:
            continue
        marker = match.group(1)
        if opened is None:
            opened = (marker[0], len(marker), number)
        elif marker[0] == opened[0] and len(marker) >= opened[1]:
            opened = None
    if opened:
        issues.append(Issue(path, opened[2], "fenced-code", "unclosed fenced code block"))
    return text, issues


def collect_pinned_links(documents: Mapping[str, str]) -> tuple[Counter[str], Counter[str], set[tuple[str, str, str]], Counter[str]]:
    digests: Counter[str] = Counter()
    repos: Counter[str] = Counter()
    files: Counter[str] = Counter()
    targets: set[tuple[str, str, str]] = set()
    for source in sorted(documents):
        for _line, label, url in extract_markdown_links(documents[source]):
            match = PINNED_URL_RE.fullmatch(url)
            if not match:
                continue
            repo, commit, target_path = match.groups()
            digests[link_fingerprint(source, label, url)] += 1
            repos[repo] += 1
            files[source] += 1
            targets.add((repo, commit, target_path))
    return digests, repos, targets, files


def check_pinned_links(
    documents: Mapping[str, str],
    approved: Counter[str] = APPROVED_PINNED_DIGESTS,
    enforce_live_baseline: bool = True,
) -> list[Issue]:
    actual, repos, targets, files = collect_pinned_links(documents)
    issues: list[Issue] = []
    if actual != approved:
        issues.append(Issue("<repository>", 0, "pinned-link", "D8 label+URL occurrence multiset changed"))
    if not enforce_live_baseline:
        return issues
    if dict(files) != EXPECTED_FILE_LINK_COUNTS:
        issues.append(Issue("<repository>", 0, "pinned-distribution", "per-file pinned counts changed"))
    if dict(repos) != EXPECTED_REPO_LINK_COUNTS:
        issues.append(Issue("<repository>", 0, "pinned-distribution", "target repository counts changed"))
    visibility = Counter()
    for repo, count in repos.items():
        visibility[REPO_VISIBILITY[repo]] += count
    if dict(visibility) != EXPECTED_VISIBILITY_COUNTS:
        issues.append(Issue("<repository>", 0, "pinned-visibility", "private/public metadata distribution changed"))
    if len(targets) != EXPECTED_PINNED_TARGETS:
        issues.append(Issue("<repository>", 0, "pinned-targets", "distinct pinned target count changed"))
    if sum(actual.values()) != 75:
        issues.append(Issue("<repository>", 0, "pinned-total", "pinned link total is not 75"))
    return issues


def check_relative_links(root: Path, documents: Mapping[str, str]) -> list[Issue]:
    issues: list[Issue] = []
    root = root.resolve()
    for source in sorted(documents):
        source_dir = (root / source).parent
        for line, _label, target in extract_markdown_links(documents[source]):
            parsed = urlsplit(target.strip("<>"))
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            decoded = unquote(parsed.path)
            if not decoded.lower().endswith(".md"):
                continue
            resolved = (source_dir / decoded).resolve()
            try:
                resolved.relative_to(root)
            except ValueError:
                issues.append(Issue(source, line, "relative-link", "relative Markdown target leaves repository root"))
                continue
            if not resolved.is_file():
                issues.append(Issue(source, line, "relative-link", "relative Markdown target is missing"))
    return issues


def check_sensitive_patterns(documents: Mapping[str, str]) -> list[Issue]:
    issues: list[Issue] = []
    for path in sorted(documents):
        for rule, pattern in SECRET_PATTERNS.items():
            for match in pattern.finditer(documents[path]):
                line = documents[path].count("\n", 0, match.start()) + 1
                issues.append(Issue(path, line, rule, "potential sensitive value detected; value suppressed"))
    return issues


def check_status_regressions(documents: Mapping[str, str]) -> list[Issue]:
    combined = "\n".join(documents.values())
    issues: list[Issue] = []
    for phrase in STALE_PHRASES:
        if phrase in combined:
            issues.append(Issue("<repository>", 0, "stale-reference", "D11I/D11L-removed status text returned"))
    for phrase in REQUIRED_CURRENT_PHRASES:
        if phrase not in combined:
            issues.append(Issue("<repository>", 0, "status-baseline", "planned/not-implemented status baseline changed"))
    return issues


def read_document_bytes(root: Path, relative: str) -> bytes:
    """Use a verified Git blob only for the known historical Windows CRLF case."""
    data = (root / relative).read_bytes()
    expected = HISTORICAL_CANONICAL_SHA256.get(relative)
    if expected is None or b"\r" not in data:
        return data
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "show", f"HEAD:{relative}"],
            check=False, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
        )
    except OSError:
        return data
    if result.returncode == 0 and hashlib.sha256(result.stdout).hexdigest() == expected:
        return result.stdout
    return data


def check_repository(root: Path) -> tuple[list[Issue], dict[str, int]]:
    root = root.resolve()
    issues: list[Issue] = []
    documents: dict[str, str] = {}
    actual_markdown = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*.md")
        if ".git" not in path.parts
    }
    if actual_markdown != set(DOC_PATHS):
        issues.append(Issue("<repository>", 0, "document-set", "tracked documentation path set changed"))
    for relative in DOC_PATHS:
        if not (root / relative).is_file():
            issues.append(Issue(relative, 0, "missing-document", "required document is missing"))
            continue
        text, file_issues = validate_document_bytes(relative, read_document_bytes(root, relative), APPROVED_HARDBREAKS)
        issues.extend(file_issues)
        if text is not None:
            documents[relative] = text
    if len(APPROVED_PINNED_DIGESTS) != 48 or sum(APPROVED_PINNED_DIGESTS.values()) != 75:
        issues.append(Issue("<checker>", 0, "baseline-definition", "pinned baseline is malformed"))
    if len(APPROVED_HARDBREAKS) != 20:
        issues.append(Issue("<checker>", 0, "baseline-definition", "hard-break baseline is malformed"))
    issues.extend(check_pinned_links(documents))
    issues.extend(check_relative_links(root, documents))
    issues.extend(check_sensitive_patterns(documents))
    issues.extend(check_status_regressions(documents))
    return sorted(set(issues)), {
        "documents": len(documents), "pinned_links": 75,
        "pinned_targets": EXPECTED_PINNED_TARGETS, "hardbreaks": 20,
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    try:
        issues, summary = check_repository(root)
    except Exception as exc:
        print(f"FAIL checker-error: {type(exc).__name__}", file=sys.stderr)
        return 2
    if issues:
        print(f"FAIL docs-integrity: {len(issues)} issue(s)", file=sys.stderr)
        for issue in issues:
            print(f"{issue.path}:{issue.line}: {issue.rule}: {issue.message}", file=sys.stderr)
        return 1
    print(
        "PASS docs-integrity: "
        f"documents={summary['documents']} pinned_links={summary['pinned_links']} "
        f"pinned_targets={summary['pinned_targets']} hardbreaks={summary['hardbreaks']} "
        "private_target_http_checks=skipped"
    )
    print("NOTE static checks do not establish copyright, provenance, human acceptance, or product implementation.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
