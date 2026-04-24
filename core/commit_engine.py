"""
core/commit_engine.py
Orchestrates the full commit generation pipeline.

ALL FIXES APPLIED (22 bugs across 3 audit rounds):
  Round 1:
  - R1B1: GIT_AUTHOR_DATE env var ignored → use author_date=/commit_date= params
  - R1B2: GIT_AUTHOR_NAME env var ignored → use Actor(name, email)
  - R1B3: repo.index.add() wrong cwd → os.chdir(repo_path) before staging
  - R1B4: FileMutator + staging dir mismatch → same os.chdir fix
  Round 2:
  - R2B2: Empty files list crash → write_placeholder() + is_dirty() guard
  - R2B5: num_commits ignored → now truncates/pads commits list
  - R2B6: select_random_files() dead → wired up when randomize=true
  Round 3:
  - B1: Padding index wrong → fixed counter loop
  - B2: ensure_files_exist only on selected files → now runs on ALL files first
  - B3: is_dirty() crashes on fresh repo → head.is_valid() guard
  - B4: Placeholder gets Python snippet appended → skip mutation for .edu_log
  - B6: Relative path staging fragile → use os.path.abspath()
"""

import os
import sys
from pathlib import Path
from git import Repo, Actor, InvalidGitRepositoryError, GitCommandError

from core.time_distributor import TimeDistributor
from core.file_mutator import FileMutator
from utils.logger import Logger

log = Logger()

PLACEHOLDER_FILE = ".edu_log"


class CommitEngine:
    def __init__(self, cfg: dict, verbose: bool = False):
        self.cfg = cfg
        self.verbose = verbose
        self.repo_path = str(Path(cfg["repo_path"]).resolve())  # Always absolute
        self.author_name = cfg["author"]["name"]
        self.author_email = cfg["author"]["email"]
        self.options = cfg["options"]
        self.dry_run = self.options.get("dry_run", False)
        self.randomize = self.options.get("randomize_file_changes", True)

        # FIX B1: Correct padding loop using fixed counter
        raw_commits = cfg["commits"]
        num_commits = self.options.get("num_commits", len(raw_commits))
        if len(raw_commits) >= num_commits:
            self.commits = raw_commits[:num_commits]
        else:
            self.commits = raw_commits[:]
            # B1 FIX: use range-based counter so modulo never shifts
            for i in range(len(raw_commits), num_commits):
                self.commits.append(raw_commits[i % len(raw_commits)])
        log.info(f"Commit count: {len(self.commits)} (num_commits={num_commits}, defined={len(raw_commits)})")

        # Actor carries correct author/committer identity (not env vars)
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

    def _is_repo_dirty(self, repo: Repo) -> bool:
        """FIX B3: Safe is_dirty() that handles fresh repos with no HEAD."""
        try:
            if not repo.head.is_valid():
                # Fresh repo — no HEAD yet, always safe to commit
                return True
            return repo.is_dirty(index=True)
        except (TypeError, ValueError):
            return True  # Assume dirty on any error — safe to proceed

    def run(self):
        """Main execution: generate all commits in the target repo."""
        repo = self._open_or_init_repo()
        timestamps = self._resolve_timestamps()

        # Switch cwd to repo_path before ALL file operations
        # GitPython resolves relative paths from cwd
        original_cwd = os.getcwd()
        os.chdir(self.repo_path)
        log.info(f"Working directory set to: {self.repo_path}")

        log.info(f"Preparing to generate {len(self.commits)} commit(s)...")
        if self.dry_run:
            log.warning("[DRY RUN] The following commits would be created:")

        try:
            for step, (commit_def, utc_time) in enumerate(zip(self.commits, timestamps), start=1):
                message = commit_def["message"]
                original_files = commit_def.get("files", [])  # Keep original list

                if self.verbose or self.dry_run:
                    log.debug(f"Step {step}: '{message}' @ UTC {utc_time} | Files: {original_files}")

                if self.dry_run:
                    continue

                # FIX B2: Always ensure ALL defined files exist BEFORE random selection
                # This prevents non-selected files from being missing on later commits
                if original_files:
                    self.mutator.ensure_files_exist(original_files)

                # Determine which files to stage for this commit
                files_to_stage = original_files[:]

                # FIX B2 (cont): Select random subset AFTER ensuring all files exist
                if self.randomize and len(files_to_stage) > 2:
                    files_to_stage = self.mutator.select_random_files(files_to_stage, k=2)
                    if self.verbose:
                        log.debug(f"  Random file selection → {files_to_stage}")

                # FIX B4: If no files, use placeholder — but skip mutation on it
                use_placeholder = not files_to_stage
                if use_placeholder:
                    placeholder = self.mutator.write_placeholder(step)
                    files_to_stage = [placeholder]
                    if self.verbose:
                        log.debug(f"  No files defined — using placeholder: {placeholder}")

                # Apply mutations only to real (non-placeholder) files
                if self.randomize and not use_placeholder:
                    self.mutator.mutate_files(files_to_stage, step)

                # FIX B6: Use abspath for cross-platform robust staging
                abs_files = [os.path.abspath(f) for f in files_to_stage]
                repo.index.add(abs_files)

                # FIX B3: Safe dirty check that handles fresh/headless repos
                if not self._is_repo_dirty(repo):
                    log.warning(f"Step {step}: Nothing staged — skipping commit")
                    continue

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
            os.chdir(original_cwd)

        if not self.dry_run:
            log.success(f"\n✅ Done! {len(self.commits)} commit(s) written to: {self.repo_path}")
            log.info("Next steps:")
            log.info("  cd into your target repo")
            log.info("  git remote add origin https://github.com/<your-username>/<new-repo>.git")
            log.info("  git push -u origin main")
        else:
            log.info("\n[DRY RUN complete] No changes were made to the repository.")
