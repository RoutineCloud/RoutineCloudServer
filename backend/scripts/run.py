"""
Routine Cloud API - Main Entry Point

This script imports the FastAPI application from app/main.py and runs it with uvicorn.
"""
import os
import sys

import pyrootutils

# Add the parent directory to sys.path to allow importing from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup root directory
root = pyrootutils.setup_root(
    search_from=__file__,
    indicator=["pyproject.toml"],
    project_root_env_var=True,
    dotenv=False,
    cwd = True
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)