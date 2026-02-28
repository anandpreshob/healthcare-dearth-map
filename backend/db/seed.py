#!/usr/bin/env python3
"""Entry point to seed the database with real NPPES/Census data and compute dearth scores.

Usage:
    python -m backend.db.seed
    # or from backend/:
    python -m db.seed
"""

import sys
import os

# Ensure the backend package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from etl.run_pipeline import run


def main():
    print("Starting database seed...")
    run()
    print("Database seed complete.")


if __name__ == "__main__":
    main()
