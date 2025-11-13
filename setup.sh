#!/usr/bin/env bash
set -e

# Install dependencies with MSSQL support (avoids psycopg2 build issues)
uv sync --all-packages --group dev --group mssql

# Install pre-commit hooks
uv run pre-commit install
uv run pre-commit install --config .commit-msg-config.yaml --hook-type commit-msg

uv pip install -e libs/database-core -e libs/storage-adapter -e libs/tenant-auth -e libs/compliance-engine
uv pip install -e libs/fastapi-core

echo "Setup complete!"


