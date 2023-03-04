#!/bin/bash
echo "Running tests..."
set -eo pipefail
python3 ../functions/input_validator/input_validator.test.py
echo "Tests completed successfully."