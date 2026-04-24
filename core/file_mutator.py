"""
core/file_mutator.py
Randomly selects files and injects realistic code snippets
to simulate genuine human development activity per commit.
"""

import os
import random
import json
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


class FileMutator:
    def __init__(self, repo_path: str, language: str = "python"):
        self.repo_path = Path(repo_path)
        self.language = language
        self.snippets = self._load_snippets(language)

    def _load_snippets(self, language: str) -> list:
        """Load code snippets from templates directory."""
        snippet_file = TEMPLATES_DIR / f"{language}_snippets.json"
        if not snippet_file.exists():
            return [f"# Auto-generated change at step {{step}}\n"]
        with open(snippet_file, "r") as f:
            data = json.load(f)
        return data.get("snippets", [])

    def ensure_files_exist(self, files: list):
        """Create files in repo if they don't exist yet."""
        for rel_path in files:
            full_path = self.repo_path / rel_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            if not full_path.exists():
                with open(full_path, "w") as f:
                    ext = Path(rel_path).suffix
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
        """
        mutated = []
        for rel_path in files:
            full_path = self.repo_path / rel_path
            if not full_path.exists():
                self.ensure_files_exist([rel_path])

            snippet = random.choice(self.snippets) if self.snippets else f"# Step {step}\n"
            snippet = snippet.replace("{step}", str(step))

            with open(full_path, "a") as f:
                f.write(f"\n{snippet}\n")

            mutated.append(rel_path)
        return mutated

    def select_random_files(self, all_files: list, k: int = 2) -> list:
        """Randomly pick k files from a list for this commit."""
        return random.sample(all_files, min(k, len(all_files)))
