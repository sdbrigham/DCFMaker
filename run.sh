#!/bin/bash
# Script to run the DCF Valuation Tool

cd "$(dirname "$0")"
source .venv/bin/activate
python app.py

