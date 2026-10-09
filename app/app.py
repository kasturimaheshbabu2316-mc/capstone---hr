"""Primary Application Entrypoint for Naukri.com Domain Support Agent.

Track: Recruitment & HR (Naukri.com)
Exports FastAPI application instance and CLI runner.
"""

import os
import sys
import uvicorn

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app

# Export app symbol
__all__ = ["app"]


def run():
    """Runs uvicorn production server."""
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    run()
