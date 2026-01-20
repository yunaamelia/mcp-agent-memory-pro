#!/bin/bash
set -e

# Get the directory of the script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$DIR/.."

# Check if python/venv exists (Priority)
if [ -d "$PROJECT_ROOT/python/venv" ]; then
    echo "Using python/venv virtual environment..."
    source "$PROJECT_ROOT/python/venv/bin/activate"
elif [ -d "$PROJECT_ROOT/.venv" ]; then
    echo "Using .venv virtual environment..."
    source "$PROJECT_ROOT/.venv/bin/activate"
fi

# Set PYTHONPATH
export PYTHONPATH="$PROJECT_ROOT/python:$PYTHONPATH"

# Start the server
echo "Starting MCP Agent Memory Pro API..."
python "$PROJECT_ROOT/python/api/server.py"
