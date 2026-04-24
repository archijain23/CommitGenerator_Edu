#!/usr/bin/env python3
"""
CommitGenerator_Edu - CLI Entry Point

🎓 EDUCATIONAL PURPOSES ONLY
This tool demonstrates Git commit metadata manipulation for learning
Git internals. Do not use for deceptive purposes.

FIX Issue 3: Use cfg.setdefault('options', {}) before assigning dry_run
  - Prevents KeyError crash when 'options' key is missing from JSON
  - Validator runs AFTER this line so we must guard here too
"""

import click
import sys
from core.validator import validate_config
from core.commit_engine import CommitEngine
from utils.logger import Logger
from utils.git_helpers import load_json_config

log = Logger()


@click.command()
@click.option(
    "--config", "-c",
    default="config/commits.json",
    help="Path to JSON config file (default: config/commits.json)",
    show_default=True,
)
@click.option(
    "--dry-run", "-d",
    is_flag=True,
    default=False,
    help="Preview commits without writing to the repository",
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    default=False,
    help="Enable verbose logging output",
)
def main(config, dry_run, verbose):
    """
    \b
    CommitGenerator_Edu
    ===================
    Generate realistic Git commits with custom timestamps.
    Reads commit definitions from a JSON config file and
    applies them to a target Git repository.

    \b
    EDUCATIONAL USE ONLY - See README for ethical guidelines.
    """
    log.banner()
    log.info(f"Loading config from: {config}")

    cfg = load_json_config(config)
    if cfg is None:
        log.error(f"Failed to load config: {config}")
        sys.exit(1)

    # FIX Issue 3: Use setdefault so we never KeyError if 'options' is missing
    # Validator runs next and will catch missing 'options' with a friendly message
    if dry_run:
        cfg.setdefault("options", {})["dry_run"] = True
        log.warning("DRY RUN mode enabled — no commits will be written")

    errors = validate_config(cfg)
    if errors:
        log.error("Config validation failed:")
        for err in errors:
            log.error(f"  → {err}")
        sys.exit(1)

    log.success("Config validated successfully")

    engine = CommitEngine(cfg, verbose=verbose)
    engine.run()


if __name__ == "__main__":
    main()
