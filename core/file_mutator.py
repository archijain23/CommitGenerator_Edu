"""
core/file_mutator.py
Randomly selects files and injects realistic code snippets
to simulate genuine human development activity per commit.

FIXES APPLIED (Round 3):
  - B5:  Fallback snippet uses language-appropriate comment syntax
  - B10: Template JSON opened with encoding='utf-8'
  - B11: All file write/append operations use encoding='utf-8'
"""

import os
import random
import json
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

# FIX B5: Language-appropriate fallback comment prefixes
COMMENT_PREFIX = {
    "python": "#",
    "js": "//",
    "javascript": "//",
    "ts": "//",
    "typescript": "//",
}


class FileMutator:
    def __init__(self, repo_path: str, language: str = "python"):
        self.repo_path = Path(repo_path)
        self.language = language
        self.snippets = self._load_snippets(language)

    def _load_snippets(self, language: str) -> list:
        """Load code snippets from templates directory."""
        snippet_file = TEMPLATES_DIR / f"{language}_snippets.json"
        if not snippet_file.exists():
            # FIX B5: Use correct comment prefix for the language
            prefix = COMMENT_PREFIX.get(language.lower(), "#")
            return [f"{prefix} Auto-generated change at step {{step}}\n"]
        # FIX B10: Explicit UTF-8 encoding for template JSON
        with open(snippet_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("snippets", [])

    def ensure_files_exist(self, files: list):
        """Create files in repo if they don't exist yet."""
        for rel_path in files:
            full_path = self.repo_path / rel_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            if not full_path.exists():
                ext = Path(rel_path).suffix
                # FIX B11: Explicit UTF-8 encoding on all file writes
                with open(full_path, "w", encoding="utf-8") as f:
                    if ext == ".py":
                        f.write(f"# {rel_path}\n# Created by CommitGenerator_Edu\n")
                    elif ext in [".js", ".ts"]:
                        f.write(f"// {rel_path}\n// Created by CommitGenerator_Edu\n")
                    elif ext == ".md":
                        f.write(f"# {Path(rel_path).stem}\n\nDocumentation placeholder.\n")
                    else:
                        f.write(f"# {rel_path}\n")

    def mutate_files(self, files: list, step: int) -> list:
        """
        Apply a random code snippet to each file in the list.
        Returns list of files that were mutated.
        NOTE: Do NOT pass placeholder files (.edu_log) to this method.
        """
        mutated = []
        for rel_path in files:
            full_path = self.repo_path / rel_path
            if not full_path.exists():
                self.ensure_files_exist([rel_path])

            snippet = random.choice(self.snippets) if self.snippets else f"# Step {step}\n"
            snippet = snippet.replace("{step}", str(step))

            # FIX B11: Explicit UTF-8 encoding on all file appends
            with open(full_path, "a", encoding="utf-8") as f:
                f.write(f"\n{snippet}\n")

            mutated.append(rel_path)
        return mutated

    def select_random_files(self, all_files: list, k: int = 2) -> list:
        """
        Randomly pick up to k files from the provided list.
        Used when randomize_file_changes=true to simulate realistic
        partial-file commits.
        NOTE: ensure_files_exist() must be called on ALL files BEFORE
        calling this method — see commit_engine.py run() for correct order.
        """
        if not all_files:
            return []
        return random.sample(all_files, min(k, len(all_files)))

    def write_placeholder(self, step: int) -> str:
        """
        Write a placeholder file when commits[] has files=[].
        Ensures there is always something staged.
        Returns the relative filename of the placeholder.
        NOTE: commit_engine skips mutate_files() on this file.
        """
        placeholder_path = self.repo_path / ".edu_log"
        # FIX B11: Explicit UTF-8 encoding
        with open(placeholder_path, "a", encoding="utf-8") as f:
            f.write(f"commit step {step}\n")
        return ".edu_log"
