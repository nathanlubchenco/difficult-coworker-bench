#!/usr/bin/env python3
"""
Entry point for difficult-coworker-bench simulation.
"""
import os
import sys

# Ensure src/ is on the import path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from difficult_coworker_bench.cli import main

if __name__ == '__main__':
    main()