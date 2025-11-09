#!/usr/bin/env python
"""
Simple launcher for the Multi-Agent Streamlit Application.
Run from the app directory: python run.py
"""

import streamlit as st
from streamlit.web import cli as stcli
import sys
import os

# Ensure we're in the right directory context
if __name__ == "__main__":
    # Add parent directory to path for utils access
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    # Run streamlit
    sys.argv = ["streamlit", "run", "main.py"]
    sys.exit(stcli.main())