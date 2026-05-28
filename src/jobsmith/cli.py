#!/usr/bin/env python
"""Command-line interface for jobsmith.

Usage:
    jobsmith submit --config_file config.toml
    jobsmith submit-scan --config_file scan_config.toml [--dry-run] [--keep-configs]

Commands:
    submit       Submit a single job from a configuration file
    submit-scan  Submit a parameter scan from a configuration file
"""

import argparse
import sys


def main():
    """Main entry point for the jobsmith CLI."""
    parser = argparse.ArgumentParser(
        description="jobsmith - Unified job submission interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Submit a single job:
    jobsmith submit --config_file config.toml

  Submit a parameter scan:
    jobsmith submit-scan --config_file scan_config.toml

  Preview scan without submitting:
    jobsmith submit-scan --config_file scan_config.toml --dry-run
"""
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # submit command
    submit_parser = subparsers.add_parser(
        "submit",
        help="Submit a single job from a configuration file"
    )
    submit_parser.add_argument(
        "--config_file",
        type=str,
        required=True,
        help="Path to the .toml configuration file"
    )
    submit_parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Keep the generated submission script after submission"
    )

    # submit-scan command
    scan_parser = subparsers.add_parser(
        "submit-scan",
        help="Submit a parameter scan from a configuration file"
    )
    scan_parser.add_argument(
        "--config_file",
        type=str,
        required=True,
        help="Path to the .toml configuration file with [scan] section"
    )
    scan_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print jobs that would be submitted without actually submitting"
    )
    scan_parser.add_argument(
        "--keep-configs",
        action="store_true",
        help="Keep generated config files after submission (default: remove them)"
    )

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    # Import here to avoid circular imports and speed up --help
    from jobsmith import submit, submit_scan

    if args.command == "submit":
        submit(args.config_file, cleanup=not args.no_cleanup)
    elif args.command == "submit-scan":
        submit_scan(
            args.config_file,
            dry_run=args.dry_run,
            keep_configs=args.keep_configs
        )


if __name__ == "__main__":
    main()
