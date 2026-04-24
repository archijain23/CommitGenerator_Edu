#!/usr/bin/env python3
"""
CommitGenerator_Edu - CLI Entry Point

🎓 EDUCATIONAL PURPOSES ONLY
This tool demonstrates Git commit metadata manipulation for learning
Git internals. Do not use for deceptive purposes.
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
    "--config",
    "-c",
    default="config/commits.json",
    help="Path to JSON config file (default: config/commits.json)",
    show_default=True,
)
@click.option(
    "--dry-run",
    "-d",
    is_flag=True,
    default=False,
    help="Preview commits without writing to the repository",
)
@click.option(
    "--verbose",
    "-v",
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

    # Load config
    cfg = load_json_config(config)
    if cfg is None:
        log.error(f"Failed to load config: {config}")
        sys.exit(1)

    # Override dry_run from CLI flag
    if dry_run:
        cfg["options"]["dry_run"] = True
        log.warning("DRY RUN mode enabled — no commits will be written")

    # Validate config
    errors = validate_config(cfg)
    if errors:
        log.error("Config validation failed:")
        for err in errors:
            log.error(f"  → {err}")
        sys.exit(1)

    log.success("Config validated successfully")

    # Run commit engine
    engine = CommitEngine(cfg, verbose=verbose)
    engine.run()


if __name__ == "__main__":
    main()
