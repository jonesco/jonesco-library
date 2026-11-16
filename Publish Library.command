#!/bin/zsh
# Double-click to publish the library to library.jonesco.com (same as the Publish button in the launcher).
cd "$(dirname "$0")" && .venv/bin/python tools/publish.py; echo; read -k 1 "?Press any key to close."
