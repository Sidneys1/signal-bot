# Building Signal-Bot

For instructions on building locally or for Docker, see the [README](./README.md).

## Publishing on PyPI

1. Ensure that the `dev` dependencies in [the project file](./pyproject.toml) are installed.
2. Build the distributable wheel with `python -m build`.
3. Upload to PyPI with `python -m twine upload dist/*`.
