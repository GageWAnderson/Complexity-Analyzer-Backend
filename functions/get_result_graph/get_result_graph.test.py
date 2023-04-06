import unittest
from unittest.mock import Mock, patch, MagicMock
import get_result_graph
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
            "body": "None",
            "isBase64Encoded": False,
        }

        context = MagicMock()
        with patch("boto3.resource") as mock_resource:
            expected_response = {
                "Body": "CSV Data Goes Here"
            }
            mock_resource.return_value.Object.return_value = expected_response
            result = get_result_graph.lambda_handler(event, context)
            self.assertEqual(
                result, {"statusCode": 200, "body": expected_response}
            )
