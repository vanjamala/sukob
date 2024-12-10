#!/usr/bin/env bash

echo "Running pyup_dirs..."
pyup_dirs --py39-plus --recursive sukob tests

echo "Running ruff linter (isort, flake, pyupgrade, etc. replacement)..."
ruff check

echo "Running ruff formatter (black replacement)..."
ruff format

echo "Running codespell to find typos..."
codespell --skip="./playwright-report"
