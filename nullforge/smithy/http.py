"""HTTP utilities for NullForge."""

CURL_ARGS = {
    "--compressed": " ",
    "--retry": "3",
    "--retry-connrefused": " ",
    "--connect-timeout": "10",
    "--max-time": "120",
    "--proto": "=https",
    "--tlsv1.2": " ",
}
"""Robust curl options for reliable downloads."""

CURL_ARGS_STR = " ".join([f"{k} {v}" if v != " " else k for k, v in CURL_ARGS.items()])
"""String representation of curl arguments."""
