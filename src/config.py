"""
Configuration loader utility for TOML-based configuration files.

This module provides utilities to load TOML configuration files and merge
them with CLI arguments. CLI arguments take precedence over config file values.

Usage:
    from src.config import load_toml_config, merge_config_and_args

    # Load config file
    config = load_toml_config("config.toml")

    # Merge with CLI args (CLI takes precedence)
    merged = merge_config_and_args(config, parsed_args)
"""

import argparse
import json
import sys


def str_to_bool(value: str) -> bool:
    """Convert a string argument to a boolean value.

    Args:
        value: String value to convert (e.g., 'true', 'false', '1', '0').

    Returns:
        Boolean value.

    Raises:
        argparse.ArgumentTypeError: If the value cannot be converted.
    """
    if isinstance(value, bool):
        return value
    if value.lower() in ('true', 'yes', '1', 'on'):
        return True
    if value.lower() in ('false', 'no', '0', 'off'):
        return False
    raise argparse.ArgumentTypeError(
        f"Invalid boolean value: '{value}'. Use 'true'/'false', 'yes'/'no', or '1'/'0'."
    )


def parse_json_array(value: str) -> list:
    """Parse a JSON array string with helpful error messages.

    Args:
        value: JSON array string (e.g., '[1, 2, 3]' or '[0.5, 1.0]').

    Returns:
        Parsed list.

    Raises:
        argparse.ArgumentTypeError: If the value is not a valid JSON array.
    """
    try:
        result = json.loads(value)
        if not isinstance(result, list):
            raise argparse.ArgumentTypeError(
                f"Expected a JSON array, got {type(result).__name__}: {value}"
            )
        return result
    except json.JSONDecodeError as e:
        raise argparse.ArgumentTypeError(
            f"Invalid JSON array: {value}. Expected format: [value1, value2, ...]. "
            f"Error: {e}"
        )


def load_toml_config(path: str) -> dict:
    """Load a TOML configuration file.

    Uses Python's built-in tomllib (Python >= 3.11) and falls back to
    the third-party tomli package for older Python versions.

    Args:
        path: Path to the TOML configuration file.

    Returns:
        Parsed configuration as a dictionary.

    Raises:
        SystemExit: If the file is not found, not valid TOML, or if tomli
                    is required but not installed.
    """
    # Try to use Python 3.11+ built-in tomllib first
    try:
        import tomllib
        toml_load = tomllib.load
        toml_decode_error = tomllib.TOMLDecodeError
    except ImportError:
        # Fall back to tomli for Python < 3.11
        try:
            import tomli
            toml_load = tomli.load
            toml_decode_error = tomli.TOMLDecodeError
        except ImportError:
            print(
                "Error: TOML parsing requires 'tomllib' (Python >= 3.11) or "
                "'tomli' package.\n"
                "Install tomli with: pip install tomli"
            )
            sys.exit(1)

    try:
        with open(path, 'rb') as f:
            return toml_load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file '{path}' not found.")
        sys.exit(1)
    except toml_decode_error as e:
        print(f"Error: Invalid TOML in '{path}': {e}")
        sys.exit(1)


def merge_config_and_args(config: dict, args: argparse.Namespace) -> dict:
    """Merge TOML configuration with CLI arguments.

    CLI arguments take precedence over config file values. An argument
    is considered "provided" if its value is not None. For boolean flags,
    explicit True/False values override config values.

    Args:
        config: Dictionary from parsed TOML config file.
        args: Namespace object from argparse.

    Returns:
        Merged configuration dictionary where CLI args override config values.

    Example:
        >>> config = {"n_turns": 1000, "beam_current": 0.5}
        >>> args = argparse.Namespace(n_turns=2000, beam_current=None)
        >>> merged = merge_config_and_args(config, args)
        >>> merged["n_turns"]  # CLI value takes precedence
        2000
        >>> merged["beam_current"]  # Config value used (CLI was None)
        0.5
    """
    # Start with a copy of the config
    merged = dict(config)

    # Iterate through all args and override config values if arg is provided
    for key, value in vars(args).items():
        # Skip the config file path itself
        if key in ('config', 'config_file'):
            continue

        # CLI arg overrides config if it's not None
        # For booleans, we consider the value as "provided" since argparse
        # will set them explicitly
        if value is not None:
            merged[key] = value

    return merged
