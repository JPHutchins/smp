# Simple Management Protocol (SMP)

## lint

### windows

```ps
. ./envr.ps1
lint
```

### linux

```bash
black --check . && isort --check-only . && flake8 . && mypy .
```
