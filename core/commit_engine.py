"""
core/commit_engine.py
Orchestrates the full commit generation pipeline:
  1. Distributes timestamps across the time window
  2. Mutates files per commit
  3. Passes author_date & commit_date directly to GitPython (env vars are ignored by GitPython)
  4. Creates Git commits in the target repo with correct author identity via Actor()

FIXES APPLIED:
  - Bug 1: GIT_AUTHOR_DATE env var ignored by GitPython → use author_date= / commit_date= params
  - Bug 2: GIT_AUTHOR_NAME env var ignored by GitPython → use Actor(name, email) object
  - Bug 3: repo.index.add() resolves relative paths from cwd → os.chdir(repo_path) before staging
  - Bug 4: FileMutator + staging must both run after cwd is set to repo_path
"""

import os
import sys
from pathlib import Path
from git import Repo, Actor, InvalidGitRepositoryError, GitCommandError

from core.time_distributor import TimeDistributor
from core.file_mutator import FileMutator
from utils.logger import Logger

log = Logger()


class CommitEngine:
    def __init__(self, cfg: dict, verbose: bool = False):
        self.cfg = cfg
        self.verbose = verbose
        self.repo_path = str(Path(cfg["repo_path"]).resolve())  # Always use absolute path
        self.author_name = cfg["author"]["name"]
        self.author_email = cfg["author"]["email"]
        self.commits = cfg["commits"]
        self.options = cfg["options"]
        self.dry_run = self.options.get("dry_run", False)

        # FIX Bug 2: Create Actor object — GitPython uses this, NOT env vars
        self.actor = Actor(self.author_name, self.author_email)

        self.distributor = TimeDistributor(cfg["time_window"])
        self.mutator = FileMutator(
            repo_path=self.repo_path,
            language=self.options.get("random_mutation_language", "python")
        )

    def _open_or_init_repo(self) -> Repo:
        """Open existing repo or initialize a new one at repo_path."""
        path = Path(self.repo_path)
        path.mkdir(parents=True, exist_ok=True)
        try:
            repo = Repo(str(path))
            log.info(f"Opened existing repo at: {path}")
        except InvalidGitRepositoryError:
            repo = Repo.init(str(path))
            log.info(f"Initialized new repo at: {path}")

        # Set repo-level git config for fallback identity
        with repo.config_writer() as cw:
            cw.set_value("user", "name", self.author_name)
            cw.set_value("user", "email", self.author_email)

        return repo

    def _resolve_timestamps(self) -> list:
        """Build the list of UTC timestamp strings for each commit."""
        n = len(self.commits)

        if self.options.get("auto_distribute_time", True):
            timestamps = self.distributor.distribute_evenly(n)
        else:
            timestamps = self.distributor.distribute_random(n)

        # Apply per-commit time_override if specified
        for i, commit_def in enumerate(self.commits):
            if "time_override" in commit_def:
                timestamps[i] = self.distributor.override_time(commit_def["time_override"])

        return timestamps

    def run(self):
        """Main execution: generate all commits in the target repo."""
        repo = self._open_or_init_repo()
        timestamps = self._resolve_timestamps()

        # FIX Bug 3 & 4: Switch cwd to repo_path ONCE before any file operations
        # GitPython resolves relative file paths from cwd, not from repo root
        original_cwd = os.getcwd()
        os.chdir(self.repo_path)
        log.info(f"Working directory set to: {self.repo_path}")

        log.info(f"Preparing to generate {len(self.commits)} commit(s)...")
        if self.dry_run:
            log.warning("[DRY RUN] The following commits would be created:")

        try:
            for step, (commit_def, utc_time) in enumerate(zip(self.commits, timestamps), start=1):
                message = commit_def["message"]
                files = commit_def.get("files", [])

                if self.verbose or self.dry_run:
                    log.debug(f"Step {step}: '{message}' @ UTC {utc_time} | Files: {files}")

                if self.dry_run:
                    continue

                # FIX Bug 4: cwd is now repo_path, so FileMutator and index.add() both work
                self.mutator.ensure_files_exist(files)
                if self.options.get("randomize_file_changes", True):
                    self.mutator.mutate_files(files, step)

                # Stage files — works correctly now that cwd == repo_path
                repo.index.add(files)

                # FIX Bug 1 & 2: Pass author_date and commit_date directly as params
                # GitPython's index.commit() accepts these as strings in ISO format
                # actor carries the correct author/committer identity (fixes Bug 2)
                try:
                    repo.index.commit(
                        message,
                        author=self.actor,
                        committer=self.actor,
                        author_date=utc_time,
                        commit_date=utc_time
                    )
                    log.success(f"[{step}/{len(self.commits)}] Committed: '{message}' @ {utc_time} UTC")
                except GitCommandError as e:
                    log.error(f"Git commit failed at step {step}: {e}")
                    sys.exit(1)

        finally:
            # Always restore original working directory
            os.chdir(original_cwd)

        if not self.dry_run:
            log.success(f"\n✅ Done! {len(self.commits)} commit(s) written to: {self.repo_path}")
            log.info("Next step: cd into your target repo and run:")
            log.info("  git remote add origin https://github.com/<your-username>/<new-repo>.git")
            log.info("  git push -u origin main")
        else:
            log.info("\n[DRY RUN complete] No changes were made to the repository.")
