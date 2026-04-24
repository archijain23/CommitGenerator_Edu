"""
core/commit_engine.py
Orchestrates the full commit generation pipeline:
  1. Respects num_commits to truncate or pad the commits list
  2. Distributes timestamps across the time window
  3. Mutates files per commit (with optional random file selection)
  4. Passes author_date & commit_date directly to GitPython via Actor()
  5. Guards against empty staged index to prevent crash

FIXES APPLIED (original 4 bugs + new 3):
  - Bug 1 [orig]: GIT_AUTHOR_DATE env var → use author_date=/commit_date= params
  - Bug 2 [orig]: GIT_AUTHOR_NAME env var → use Actor(name, email) object
  - Bug 3 [orig]: repo.index.add() cwd → os.chdir(repo_path) before staging
  - Bug 4 [orig]: FileMutator + staging dir mismatch → same os.chdir fix
  - Issue 2 [new]: Empty files list → write_placeholder() ensures always staged
  - Issue 5 [new]: num_commits now respected — truncates/pads commits list
  - Issue 6 [new]: select_random_files() wired up when randomize_file_changes=true
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
        self.repo_path = str(Path(cfg["repo_path"]).resolve())
        self.author_name = cfg["author"]["name"]
        self.author_email = cfg["author"]["email"]
        self.options = cfg["options"]
        self.dry_run = self.options.get("dry_run", False)

        # FIX Issue 5: Respect num_commits — truncate or pad commits list
        raw_commits = cfg["commits"]
        num_commits = self.options.get("num_commits", len(raw_commits))
        if len(raw_commits) >= num_commits:
            # Truncate to num_commits
            self.commits = raw_commits[:num_commits]
        else:
            # Pad by cycling through existing commits
            self.commits = raw_commits[:]
            while len(self.commits) < num_commits:
                self.commits.append(raw_commits[len(self.commits) % len(raw_commits)])
        log.info(f"Commit count: {len(self.commits)} (num_commits={num_commits}, defined={len(raw_commits)})")

        # FIX Bug 2: Actor carries correct author/committer identity
        self.actor = Actor(self.author_name, self.author_email)

        self.distributor = TimeDistributor(cfg["time_window"])
        self.mutator = FileMutator(
            repo_path=self.repo_path,
            language=self.options.get("random_mutation_language", "python")
        )
        self.randomize = self.options.get("randomize_file_changes", True)

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

        with repo.config_writer() as cw:
            cw.set_value("user", "name", self.author_name)
            cw.set_value("user", "email", self.author_email)
        return repo

    def _resolve_timestamps(self) -> list:
        """Build list of UTC ISO 8601 timestamp strings for each commit."""
        n = len(self.commits)
        if self.options.get("auto_distribute_time", True):
            timestamps = self.distributor.distribute_evenly(n)
        else:
            timestamps = self.distributor.distribute_random(n)

        for i, commit_def in enumerate(self.commits):
            if "time_override" in commit_def:
                timestamps[i] = self.distributor.override_time(commit_def["time_override"])
        return timestamps

    def run(self):
        """Main execution: generate all commits in the target repo."""
        repo = self._open_or_init_repo()
        timestamps = self._resolve_timestamps()

        # FIX Bug 3 & 4: Switch cwd to repo_path ONCE before any file operations
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

                # FIX Issue 6: Use select_random_files() when randomize=true and >2 files
                if self.randomize and len(files) > 2:
                    files = self.mutator.select_random_files(files, k=2)
                    if self.verbose:
                        log.debug(f"  Random file selection → {files}")

                # FIX Issue 2: If no files defined, write placeholder to ensure
                # something is always staged (prevents 'nothing to commit' crash)
                if not files:
                    placeholder = self.mutator.write_placeholder(step)
                    files = [placeholder]
                    if self.verbose:
                        log.debug(f"  No files defined — using placeholder: {placeholder}")

                # Ensure files exist on disk and apply mutations
                self.mutator.ensure_files_exist(files)
                if self.randomize:
                    self.mutator.mutate_files(files, step)

                # Stage files (cwd is already repo_path so relative paths work)
                repo.index.add(files)

                # FIX Issue 2 (safety net): Only commit if something is actually staged
                if not repo.is_dirty(index=True):
                    log.warning(f"Step {step}: Nothing staged after mutations — skipping commit")
                    continue

                # FIX Bug 1 & 2: author_date/commit_date as params + Actor for identity
                try:
                    repo.index.commit(
                        message,
                        author=self.actor,
                        committer=self.actor,
                        author_date=utc_time,
                        commit_date=utc_time
                    )
                    log.success(f"[{step}/{len(self.commits)}] '{message}' @ {utc_time} UTC")
                except GitCommandError as e:
                    log.error(f"Git commit failed at step {step}: {e}")
                    sys.exit(1)

        finally:
            # Always restore original working directory
            os.chdir(original_cwd)

        if not self.dry_run:
            log.success(f"\n✅ Done! {len(self.commits)} commit(s) written to: {self.repo_path}")
            log.info("Next steps:")
            log.info("  cd into your target repo")
            log.info("  git remote add origin https://github.com/<your-username>/<new-repo>.git")
            log.info("  git push -u origin main")
        else:
            log.info("\n[DRY RUN complete] No changes were made to the repository.")
