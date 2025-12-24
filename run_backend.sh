#!/bin/bash
# Run the FastAPI backend server

cd "$(dirname "$0")"
python -m uvicorn backend.main:app --reload --port 8000

