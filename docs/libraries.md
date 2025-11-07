# Production Dependencies

## Web Framework & API
- [fastapi](https://fastapi.tiangolo.com/): Web framework for building APIs
- [uvicorn](https://www.uvicorn.org/): ASGI server implementation
- [asgi-correlation-id](https://github.com/snok/asgi-correlation-id): Correlation ID middleware for ASGI applications

## Data Handling & Validation
- [pydantic](https://docs.pydantic.dev/): Data validation using Python type annotations
- [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/): Settings management using Pydantic
- [orjson](https://github.com/ijl/orjson): Fast JSON parsing/serialization library

## Logging & Terminal Output
- [structlog](https://www.structlog.org/): Structured logging library
- [rich](https://rich.readthedocs.io/): Rich text and beautiful formatting in the terminal
- [colorama](https://github.com/tartley/colorama): Cross-platform colored terminal output

# Development Dependencies

## Code Quality & Analysis
- [ruff](https://docs.astral.sh/ruff/): Fast Python linter and code formatter
- [pylint](https://www.pylint.org/): Python code analysis tool
- [mypy](https://mypy.readthedocs.io/): Static type checker for Python
- [bandit](https://bandit.readthedocs.io/): Security vulnerability scanner for Python code

## Testing
- [pytest](https://docs.pytest.org/): Testing framework

## Git & Commit Management
- [pre-commit](https://pre-commit.com/): Git hooks framework
- [commitizen](https://commitizen-tools.github.io/commitizen/): Standardizing commit messages
- [commitlint](https://github.com/jorisroovers/gitlint): Lint commit messages

## Build & Task Management
- [poethepoet](https://github.com/nat-n/poethepoet): Task runner and build tool helper
- [hatchling](https://hatch.pypa.io/latest/): Modern Python build backend
- [uv-dynamic-versioning](https://github.com/astral-sh/uv): Version management using UV
- [hatch-vcs](https://github.com/ofek/hatch-vcs): VCS-based version management for Hatch

# Project Requirements
- Python: >= 3.12.4

# Project Structure
The monorepo is managed using UV workspace with:
- libs/: Shared libraries
- apps/: Applications