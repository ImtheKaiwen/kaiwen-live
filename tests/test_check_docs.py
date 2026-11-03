from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_docs  # noqa: E402


class HealthyRepositoryTests(unittest.TestCase):
    def test_six_document_live_baseline_is_75_12_20(self) -> None:
        issues, summary = check_docs.check_repository(ROOT)
        self.assertEqual(issues, [])
        self.assertEqual(summary, {"documents": 6, "pinned_links": 75, "pinned_targets": 12, "hardbreaks": 20})


class DocumentFormatTests(unittest.TestCase):
    def rules(self, data: bytes, approved=None) -> set[str]:
        _text, issues = check_docs.validate_document_bytes("sample.md", data, approved)
        return {issue.rule for issue in issues}

    def test_valid_lf_utf8_fence_and_approved_hardbreak(self) -> None:
        line = "approved break  "
        approved = {("sample.md", 2): check_docs.line_fingerprint(line)}
        self.assertEqual(self.rules(f"# Başlık\n{line}\n```text\nok\n```\n".encode(), approved), set())

    def test_bom_crlf_and_final_newline_failures(self) -> None:
        self.assertIn("utf8-bom", self.rules(b"\xef\xbb\xbf# title\n"))
        self.assertIn("line-ending", self.rules(b"# title\r\n"))
        self.assertIn("final-newline", self.rules(b"# title"))
        self.assertIn("final-newline", self.rules(b"# title\n\n"))

    def test_unbalanced_fence_and_unapproved_space_fail(self) -> None:
        self.assertIn("fenced-code", self.rules(b"# title\n```text\nopen\n"))
        self.assertIn("trailing-whitespace", self.rules(b"# title \n"))

    def test_changed_approved_hardbreak_fails(self) -> None:
        approved = {("sample.md", 1): check_docs.line_fingerprint("original  ")}
        self.assertIn("trailing-whitespace", self.rules(b"changed  \n", approved))
        self.assertIn("hardbreak-baseline", self.rules(b"changed  \n", approved))


class PinnedLinkTests(unittest.TestCase):
    SOURCE = "README.md"
    LABEL = "Pinned"
    URL = "https://github.com/ImtheKaiwen/kaiwen-ai/blob/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa/docs/ONE.md"

    def issues(self, text: str, approved=None):
        digest = check_docs.link_fingerprint(self.SOURCE, self.LABEL, self.URL)
        return check_docs.check_pinned_links(
            {self.SOURCE: text}, approved or Counter({digest: 1}), enforce_live_baseline=False
        )

    def test_exact_link_passes_and_nonledger_url_is_ignored(self) -> None:
        text = f"[{self.LABEL}]({self.URL})\n[Mutable](https://github.com/ImtheKaiwen/kaiwen-design/blob/main/README.md)\n"
        self.assertEqual(self.issues(text), [])

    def test_label_commit_path_missing_and_duplicate_fail(self) -> None:
        for text in (
            f"[Changed]({self.URL})\n",
            f"[{self.LABEL}]({self.URL.replace('a' * 40, 'b' * 40)})\n",
            f"[{self.LABEL}]({self.URL.replace('ONE.md', 'TWO.md')})\n",
            "no link\n",
            f"[{self.LABEL}]({self.URL})\n[{self.LABEL}]({self.URL})\n",
        ):
            self.assertTrue(self.issues(text))

    def test_private_public_distribution_error_is_detected(self) -> None:
        docs = {"README.md": f"[{self.LABEL}]({self.URL})\n"}
        self.assertTrue(check_docs.check_pinned_links(docs, enforce_live_baseline=True))

    def test_fenced_pseudo_link_is_ignored(self) -> None:
        self.assertTrue(self.issues(f"```markdown\n[{self.LABEL}]({self.URL})\n```\n"))


class RelativeLinkTests(unittest.TestCase):
    def test_existing_fragment_passes_missing_and_traversal_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); (root / "docs").mkdir()
            (root / "docs/target.md").write_text("ok\n", encoding="utf-8", newline="\n")
            self.assertEqual(check_docs.check_relative_links(root, {"README.md": "[T](docs/target.md#x)\n"}), [])
            self.assertTrue(check_docs.check_relative_links(root, {"README.md": "[M](docs/missing.md)\n"}))
            self.assertTrue(check_docs.check_relative_links(root, {"README.md": "[X](../outside.md)\n"}))

    def test_fenced_missing_and_remote_private_are_not_accessed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            docs = {"README.md": "```md\n[M](missing.md)\n```\n[P](https://github.com/ImtheKaiwen/private/blob/x/a.md)\n"}
            with mock.patch("socket.create_connection", side_effect=AssertionError("network used")):
                self.assertEqual(check_docs.check_relative_links(Path(temp), docs), [])


class SensitiveAndStatusTests(unittest.TestCase):
    def test_fake_pat_key_and_signed_url_are_detected_without_echo(self) -> None:
        values = ["ghp_" + "A" * 32, "-----BEGIN PRIVATE KEY-----", "https://x.invalid/a?token=" + "z" * 20]
        issues = check_docs.check_sensitive_patterns({"README.md": "\n".join(values) + "\n"})
        self.assertEqual(len(issues), 3)
        self.assertTrue(all(value not in " ".join(i.message for i in issues) for value in values))

    def test_safe_placeholder_is_allowed(self) -> None:
        self.assertEqual(check_docs.check_sensitive_patterns({"README.md": "file:///REPLACE_WITH_DATASET/dataset.lock\n"}), [])

    def test_stale_status_fails_and_current_planned_status_passes(self) -> None:
        self.assertTrue(check_docs.check_status_regressions({"README.md": "Henüz oluşturulacak.\n"}))
        current = "\n".join(check_docs.REQUIRED_CURRENT_PHRASES) + "\n"
        self.assertEqual(check_docs.check_status_regressions({"README.md": current}), [])


class HistoricalFallbackTests(unittest.TestCase):
    def test_only_verified_historical_blob_can_replace_crlf_view(self) -> None:
        canonical = b"historical\n"
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); (root / "README.upstream-20261030.md").write_bytes(b"historical\r\n")
            old = check_docs.HISTORICAL_CANONICAL_SHA256["README.upstream-20261030.md"]
            check_docs.HISTORICAL_CANONICAL_SHA256["README.upstream-20261030.md"] = hashlib.sha256(canonical).hexdigest()
            try:
                result = subprocess.CompletedProcess([], 0, canonical, b"")
                with mock.patch.object(check_docs.subprocess, "run", return_value=result):
                    self.assertEqual(check_docs.read_document_bytes(root, "README.upstream-20261030.md"), canonical)
            finally:
                check_docs.HISTORICAL_CANONICAL_SHA256["README.upstream-20261030.md"] = old

    def test_other_document_never_uses_git_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp); (root / "README.md").write_bytes(b"current\r\n")
            with mock.patch.object(check_docs.subprocess, "run") as run:
                self.assertEqual(check_docs.read_document_bytes(root, "README.md"), b"current\r\n")
                run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
