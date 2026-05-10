# Installing External Python Packages into Hermes's Stripped Venv

Hermes Agent's venv (`~/.hermes/hermes-agent/venv/`) is stripped for distribution size — no `pip` binary, no build tools. When you need to install an external Python project or dependency into Hermes's environment (e.g., a companion project like Molin-OS that runs alongside Hermes), follow this procedure.

## When to Use This

- Installing a companion Python project that Hermes needs to `import` or run via `python -m`
- Adding a Python dependency that Hermes tools or skills reference
- NOT for system-wide Python packages (use system pip) or isolated projects (use their own venv)

## Procedure

### Step 1: Bootstrap pip

The venv has setuptools but no pip binary. Bootstrap it:

```bash
~/.hermes/hermes-agent/venv/bin/python -m ensurepip
```

Verify:

```bash
~/.hermes/hermes-agent/venv/bin/python -m pip --version
```

Note: `venv/bin/pip` won't exist — always use `venv/bin/python -m pip`.

### Step 2: Install the package (editable preferred)

Use editable install (`-e`) so code changes take effect immediately without reinstall:

```bash
~/.hermes/hermes-agent/venv/bin/python -m pip install -e /path/to/project
```

For non-editable:

```bash
~/.hermes/hermes-agent/venv/bin/python -m pip install /path/to/project
```

### Step 3: Verify imports work

```bash
~/.hermes/hermes-agent/venv/bin/python -c "import package_name; print('OK')"
```

## Common Pitfalls

### `No such file or directory: .../venv/bin/pip`

Always use `python -m pip`, never `venv/bin/pip`. The binary is stripped.

### `externally-managed-environment` error

Happens when targeting the uv-managed Python (e.g., `~/.local/bin/python3.11`) instead of the Hermes venv. Always use `~/.hermes/hermes-agent/venv/bin/python`.

### Missing `__version__` in editable install

Some projects reference `__version__` in `__main__.py` but don't define it in `__init__.py`. Check and add if needed:

```python
__version__ = "X.Y.Z"
```

### Package conflicts with Hermes's own dependencies

Hermes bundles specific versions of `rich`, `requests`, `pydantic`, etc. Test the import before assuming it works. If a newer version is needed, install with `--upgrade` but be aware it might affect Hermes behavior.

### Python version mismatch

Hermes ships with Python 3.11 on macOS/Linux. Packages requiring Python 3.12+ won't install. Check `python_requires` in the project's `setup.py` or `pyproject.toml`.
