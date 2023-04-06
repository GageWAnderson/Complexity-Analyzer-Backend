import unittest
from unittest.mock import Mock, patch, MagicMock
import input_validator
import json


class TestLambdaFunction(unittest.TestCase):
    def test_lambda_function(self):
        event = {
            "resource": "/{proxy+}",
            "path": "/path/to/resource",
            "httpMethod": "POST",
            "headers": {"Content-Type": "application/json"},
            "queryStringParameters": {"uuid": "12345"},
            "pathParameters": {"proxy": "path/to/resource"},
            "stageVariables": {"baz": "qux"},
            "requestContext": {"authorizer": {"principalId": "user"}},
            "body": json.dumps(
                {
                    "inputCode": "low = 0\nhigh = len(arr) - 1\nwhile low <= high:\n    mid = (low + high) // 2\n    if arr[mid] == x:\n        return mid\n    elif arr[mid] < x:\n        low = mid + 1\n    else:\n        high = mid - 1\nreturn -1\n",
                    "args": [
                        {"argName": "arr", "argType": "list<int>", "variable": True},
                        {"argName": "x", "argType": "int", "variable": False},
                    ],
                    "maxInputSize": 10000,
                    "user-id": "1234",
                    "description": "Binary Search Test",
                }
            ),
            "isBase64Encoded": False,
        }

        context = MagicMock()
        mock_lambda = Mock()
        with patch("boto3.client") as mock_client:
            mock_client.return_value = mock_lambda
            expected_response = {
                "statusCode": 200,
                "body": "Input code passed security check",
            }
            mock_lambda.invoke.return_value = expected_response
            result = input_validator.lambda_handler(event, context)
            self.assertEqual(result, {"statusCode": 200, "body": "Input code passed security check"})
