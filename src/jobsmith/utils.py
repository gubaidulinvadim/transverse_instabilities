"""Shared utility functions for TOML configuration handling.

This module provides common functions for loading and writing TOML configuration
files used across the jobsmith submission system.
"""

import sys
import tomllib

import numpy as np


def write_toml(data: dict, filepath: str) -> None:
    """Write a dictionary to a TOML file.

    Args:
        data: Dictionary to write.
        filepath: Path to the output file.
    """
    def format_value(value):
        if isinstance(value, bool):
            return 'true' if value else 'false'
        elif isinstance(value, str):
            return f'"{value}"'
        elif isinstance(value, (int, float, np.integer, np.floating)):
            return str(value)
        elif isinstance(value, list):
            items = ', '.join(format_value(item) for item in value)
            return f'[{items}]'
        else:
            return str(value)

    with open(filepath, 'w') as f:
        # Write top-level key-value pairs
        for key, value in data.items():
            if not isinstance(value, dict):
                f.write(f'{key} = {format_value(value)}\n')

        # Write sections
        for key, value in data.items():
            if isinstance(value, dict):
                f.write(f'\n[{key}]\n')
                for subkey, subvalue in value.items():
                    f.write(f'{subkey} = {format_value(subvalue)}\n')


def load_config(config_file: str) -> dict:
    """Load and parse a .toml configuration file.

    Args:
        config_file: Path to the .toml configuration file.

    Returns:
        Parsed configuration dictionary.

    Raises:
        SystemExit: If the configuration file is not found or invalid.
    """
    try:
        with open(config_file, 'rb') as f:
            return tomllib.load(f)
    except FileNotFoundError:
        print(f"Error: Configuration file '{config_file}' not found.")
        sys.exit(1)
    except tomllib.TOMLDecodeError as e:
        print(f"Error: Invalid TOML in '{config_file}': {e}")
        sys.exit(1)


def validate_config(config: dict, config_file: str = "") -> None:
    """Validate that required configuration sections exist.

    Args:
        config: Configuration dictionary to validate.
        config_file: Path to the configuration file (for error messages).

    Raises:
        SystemExit: If required sections are missing.
    """
    file_info = f" in '{config_file}'" if config_file else ""
    if 'script' not in config:
        print(f"Error: Required [script] section missing{file_info}.")
        sys.exit(1)
    if 'job' not in config:
        print(f"Error: Required [job] section missing{file_info}.")
        sys.exit(1)
