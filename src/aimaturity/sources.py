"""Where evidence comes from: a checked-out repository (read-only) or a manifest of synthetic files.

``RepoSource`` never writes, never runs code from the target and only reads files that git tracks
(falling back to a filtered walk when the folder is not a git checkout).
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

SKIP = {".git", ".venv", "venv", "node_modules", ".terraform", "__pycache__", ".pytest_cache", ".ruff_cache", "dist", "build"}
TEXT = {
    ".md",
    ".py",
    ".yml",
    ".yaml",
    ".json",
    ".jsonl",
    ".tf",
    ".bicep",
    ".hcl",
    ".toml",
    ".txt",
    ".lock",
    ".kql",
    ".cs",
    ".ts",
    ".sh",
    ".tmdl",
    ".ipynb",
    "",
}
MAX_BYTES = 400_000


@dataclass
class RepoSource:
    name: str
    path: Path

    def files(self) -> list[str]:
        try:
            out = subprocess.run(["git", "-C", str(self.path), "ls-files"], capture_output=True, text=True, check=True).stdout.split("\n")
            files = [f for f in out if f]
        except (subprocess.CalledProcessError, FileNotFoundError):
            files = [str(p.relative_to(self.path)) for p in self.path.rglob("*") if p.is_file() and not SKIP & set(p.parts)]
        return sorted(f for f in files if Path(f).suffix in TEXT or Path(f).name in {"Dockerfile", "Makefile", "CODEOWNERS"})

    def read(self, rel: str) -> str:
        p = self.path / rel
        if not p.is_file() or p.stat().st_size > MAX_BYTES:
            return ""
        return p.read_text(errors="ignore")


@dataclass
class ManifestSource:
    """A synthetic repository described as {relative path: content}; used for the fictional sample orgs."""

    name: str
    contents: dict[str, str] = field(default_factory=dict)

    def files(self) -> list[str]:
        return sorted(self.contents)

    def read(self, rel: str) -> str:
        return self.contents.get(rel, "")
