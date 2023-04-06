import unittest
from unittest.mock import MagicMock
import code_security_validator
import json


class TestLambdaFunction(unittest.TestCase):
    def test_lambda_function(self):
        event = {
            "resource": "/{proxy+}",
            "path": "/path/to/resource",
            "httpMethod": "POST",
            "headers": {"Content-Type": "application/json"},
            "queryStringParameters": {"foo": "bar"},
            "pathParameters": {"proxy": "path/to/resource"},
            "stageVariables": {"baz": "qux"},
            "requestContext": {"authorizer": {"principalId": "user"}},
            "body": json.dumps(
                {
                    "inputCode": "low = 0\nhigh = len(arr) - 1\nwhile low <= high:\n    mid = (low + high) // 2\n    if arr[mid] == x:\n        return mid\n    elif arr[mid] < x:\n        low = mid + 1\n    else:\n        high = mid - 1\nreturn -1\n",
                    "args": [
                        {"argName": "arr", "argType": "list<int>", "variable": True},
                        {"argName": "x", "argType": "int", "variable": False},
                    ]
                }
            ),
            "isBase64Encoded": False,
        }

        context = MagicMock()
        result = code_security_validator.lambda_handler(event, context)
        self.assertEqual(result, {"statusCode": 200, "body": "Input code passed security check"})
