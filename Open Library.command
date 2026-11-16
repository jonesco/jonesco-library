#!/bin/zsh
cd "$(dirname "$0")" && exec .venv/bin/python tools/serve.py
