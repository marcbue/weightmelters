#!/bin/bash
set -e

# Copy host gitconfig if available
if [ -f "${HOME}/.gitconfig" ]; then
    cp "${HOME}/.gitconfig" /root/.gitconfig 2>/dev/null || true
fi

# Mark workspace as safe
git config --system --get-all safe.directory | grep -qx '/workspaces/weightmelters' || \
    git config --system --add safe.directory /workspaces/weightmelters || true

# Git global config
git config --global pull.rebase false

# Load environment variables from .env if it exists
if [ -f /workspaces/weightmelters/.env ]; then
    export $(grep -v '^#' /workspaces/weightmelters/.env | xargs)
fi
