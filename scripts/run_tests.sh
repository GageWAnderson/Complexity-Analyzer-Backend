#!/bin/bash
echo "Running tests..."
set -eo pipefail
python3 ../functions/input_validator/input_validator.test.py
python3 ../functions/code_security_validator/code_security_validator.test.py
python3 ../functions/get_all_user_metadata/get_all_user_metadata.test.py
python3 ../functions/get_result_graph/get_result_graph.test.py
python3 ../functions/get_results_info/get_results_info.test.py
python3 ../functions/post_complexity_analyzer_results/post_complexity_analyzer_results.test.py
python3 ../functions/code_complexity_analyzer/code_complexity_analyzer.test.py
echo "Tests completed successfully."