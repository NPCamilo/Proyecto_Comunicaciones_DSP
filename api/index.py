"""
api/index.py — Entrypoint ASGI para Vercel Serverless Functions.
"""

from __future__ import annotations

import os
import pathlib
import sys
import tempfile

# Evitar errores de matplotlib en entorno serverless
os.environ.setdefault("MPLCONFIGDIR", tempfile.gettempdir())

import matplotlib
matplotlib.use("Agg")

ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.main import app

# Exportar app para el runtime de Vercel
__all__ = ["app"]
