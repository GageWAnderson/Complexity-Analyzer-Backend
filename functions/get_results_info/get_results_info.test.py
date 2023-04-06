import unittest
from unittest.mock import Mock, patch, MagicMock
import get_results_info
import json


class TestLambdaFunction(unittest.TestCase):
    def test_lambda_function(self):
        event = {
            "resource": "/{proxy+}",
            "path": "/path/to/resource",
            "httpMethod": "POST",
            "headers": {"Content-Type": "application/json"},
            "queryStringParameters": {"uuid": "12345", "timestamp": "12345"},
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
                }
            ),
            "isBase64Encoded": False,
        }

        context = MagicMock()
        mock_client = Mock()
        with patch("boto3.resource") as mock_resource:
            mock_resource.return_value.Table.return_value = mock_client
            expected_response = {
                "Item": [
                    {
                        "uuid": "12345",
                        "metadata": {
                            "inputCode": "low = 0\nhigh = len(arr) - 1\nwhile low <= high:\n    mid = (low + high) // 2\n    if arr[mid] == x:\n        return mid\n    elif arr[mid] < x:\n        low = mid + 1\n    else:\n        high = mid - 1\nreturn -1\n",
                            "args": [
                                {
                                    "argName": "arr",
                                    "argType": "list<int>",
                                    "variable": True,
                                },
                                {"argName": "x", "argType": "int", "variable": False},
                            ],
                        },
                    }
                ]
            }
            mock_client.get_item.return_value = expected_response
            result = get_results_info.lambda_handler(event, context)
            self.assertEqual(
                result, {"statusCode": 200, "body": expected_response}
            )
