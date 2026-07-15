"""camas task definitions for smp — https://github.com/JPHutchins/camas."""

from pathlib import Path

from camas import Claude, Config, Parallel, Sequential, Task

format = Task("uv run ruff format {paths}", mutates=True, paths=".")
format_check = Task("uv run ruff format --check {paths}", paths=".")
lint = Task("uv run ruff check {paths}", paths=".")
lint_fix = Task("uv run ruff check --fix {paths}", mutates=True, paths=".")
fix = Sequential(lint_fix, format)

mypy = Task("uv run mypy src tests")
pyright = Task("uv run pyright src tests")
typecheck = Parallel(mypy, pyright)
test = Task("uv run pytest")
coverage = Task("uv run pytest --cov=smp --cov-report=term-missing --cov-report=xml")
docs = Task("uv run --group doc mkdocs build")

check = Parallel(format_check, lint, typecheck, test)
gate = Parallel(format_check, lint, typecheck, coverage)
fast = Sequential(format_check, Parallel(lint, typecheck))
all = Sequential(fix, Parallel(typecheck, coverage))

matrix = Parallel(
    Task("uv sync"),
    check,
    env={"UV_PROJECT_ENVIRONMENT": ".venv-{PY}", "UV_PYTHON": "{PY}"},
    matrix={
        "PY": tuple(
            stripped
            for line in (Path(__file__).parent / ".python-version").read_text().splitlines()
            if (stripped := line.strip()) and not stripped.startswith("#")
        )
    },
)

_ = Config(default_task=fast, github_task=check, agent=Claude(fix=fix, check=gate))
