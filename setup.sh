#!/usr/bin/env bash
set -e

# Install dependencies
uv sync --all-packages

# Install pre-commit hooks
uv run pre-commit install
uv run pre-commit install --config .commit-msg-config.yaml --hook-type commit-msg

echo "Setup complete!"
