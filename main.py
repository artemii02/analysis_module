from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'src'))

from interview_analysis.main import app  # noqa: E402


if __name__ == '__main__':
    import uvicorn

    uvicorn.run('interview_analysis.main:app', app_dir='src', host='127.0.0.1', port=8000, reload=True)
