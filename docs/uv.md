# uv

## Package Management:
1. `uv init` - Initialize a new Python project
2. `uv add [package]` - Add packages to the project
    - Examples: `uv add pytest --dev`, `uv add fastapi uvicorn pydantic`
3. `uv remove [package]` - Remove packages from the project
    - Example: `uv remove hatch --dev`
4. `uv sync` - Synchronize dependencies
    - Variations: `uv sync --all-packages`, `uv sync --group prod`
5. `uv lock --upgrade` - Update and lock dependencies
6. `uv tree` - Show dependency tree
    - Variations: `uv tree --depth=1`
 7. `uv tree --outdated --depth=1` - Show outdated dependencies

## Environment Management:
1. `uv venv` - Create a virtual environment
2. `uv --version` - Check UV version
3. `uv cache dir` - Show cache directory location

## Build and Run:
1. `uv build` - Build the project
    - Variations: `uv build --wheel`, `uv build --all-packages`
2. `uv run [command]` - Run Python commands or scripts
    - Examples:
    - `uv run poe start`
    - `uv run poe lint`
    - `uv run poe format`
    - `uv run mypy .`
    - `uv run pylint .`

## Pip Operations:
1. `uv pip install` - Install packages using pip compatibility mode
    - Example: `uv pip install --no-cache-dir ./*.whl`
