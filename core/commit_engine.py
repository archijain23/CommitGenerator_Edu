"""
core/commit_engine.py
Orchestrates the full commit generation pipeline:
  1. Distributes timestamps across the time window
  2. Mutates files per commit
  3. Sets GIT_AUTHOR_DATE and GIT_COMMITTER_DATE
  4. Creates Git commits in the target repo
"""

import os
import sys
from pathlib import Path
from git import Repo, InvalidGitRepositoryError, GitCommandError

from core.time_distributor import TimeDistributor
from core.file_mutator import FileMutator
from utils.logger import Logger

log = Logger()


class CommitEngine:
    def __init__(self, cfg: dict, verbose: bool = False):
        self.cfg = cfg
        self.verbose = verbose
        self.repo_path = cfg["repo_path"]
        self.author_name = cfg["author"]["name"]
        self.author_email = cfg["author"]["email"]
        self.commits = cfg["commits"]
        self.options = cfg["options"]
        self.dry_run = self.options.get("dry_run", False)

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

        # Set author config
        repo.config_writer().set_value("user", "name", self.author_name).release()
        repo.config_writer().set_value("user", "email", self.author_email).release()
        return repo

    def _resolve_timestamps(self) -> list:
        """Build the list of UTC timestamp strings for each commit."""
        n = len(self.commits)

        # If auto_distribute_time, spread evenly; else use random
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

        log.info(f"Preparing to generate {len(self.commits)} commit(s)...")
        if self.dry_run:
            log.warning("[DRY RUN] The following commits would be created:")

        for step, (commit_def, utc_time) in enumerate(zip(self.commits, timestamps), start=1):
            message = commit_def["message"]
            files = commit_def.get("files", [])

            if self.verbose or self.dry_run:
                log.debug(f"Step {step}: '{message}' @ UTC {utc_time} | Files: {files}")

            if self.dry_run:
                continue

            # Ensure files exist and mutate if enabled
            self.mutator.ensure_files_exist(files)
            if self.options.get("randomize_file_changes", True):
                self.mutator.mutate_files(files, step)

            # Stage files
            repo.index.add(files)

            # Set Git date environment variables
            os.environ["GIT_AUTHOR_DATE"] = utc_time
            os.environ["GIT_COMMITTER_DATE"] = utc_time
            os.environ["GIT_AUTHOR_NAME"] = self.author_name
            os.environ["GIT_AUTHOR_EMAIL"] = self.author_email
            os.environ["GIT_COMMITTER_NAME"] = self.author_name
            os.environ["GIT_COMMITTER_EMAIL"] = self.author_email

            try:
                repo.index.commit(message)
                log.success(f"[{step}/{len(self.commits)}] Committed: '{message}' @ {utc_time} UTC")
            except GitCommandError as e:
                log.error(f"Git commit failed at step {step}: {e}")
                sys.exit(1)

        if not self.dry_run:
            log.success(f"\n✅ Done! {len(self.commits)} commit(s) written to: {self.repo_path}")
            log.info("Next step: cd into your repo and run: git remote add origin <url> && git push -u origin main")
        else:
            log.info("\n[DRY RUN complete] No changes were made to the repository.")
