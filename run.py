#!/usr/bin/env python3
"""
GlobeTrotter — Desktop App Entry Point
Run with:  python run.py
"""
import sys
import os

# Ensure project root is on PYTHONPATH regardless of CWD
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ui.app import run_app

if __name__ == "__main__":
    run_app()
