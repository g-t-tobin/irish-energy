#!/usr/bin/env python3
"""
Entry point for the Irish Energy Analytics API
"""

import os
import sys
from pathlib import Path

# Add the api directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "api"))

from api.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)