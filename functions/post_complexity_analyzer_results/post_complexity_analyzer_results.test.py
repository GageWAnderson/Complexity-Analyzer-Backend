import unittest
from unittest.mock import Mock, MagicMock, patch
import post_complexity_analyzer_results
import json

class TestMyFunction(unittest.TestCase):
    @patch('boto3.resource')
    def test_post_complexity_analyzer_results(self, mock_resource):
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
        # Create mock objects for S3 and DynamoDB
        mock_s3 = Mock()
        mock_dynamodb = Mock()
        # Set the clients for the boto3 S3 and DynamoDB resources
        mock_resource.side_effect = [mock_s3, mock_dynamodb]
        
        # Define the expected responses from S3 and DynamoDB
        expected_s3_response = b'My S3 Data'
        expected_dynamodb_response = {'id': 'my-id', 'name': 'my-name', 'value': 42}
        mock_s3.Bucket.return_value = {'Body': expected_s3_response}
        mock_s3.Object.return_value = {'Body': expected_s3_response}
        mock_s3.Object.put.return_value = {'Body': expected_s3_response}
        mock_dynamodb.Table.return_value = {'Item': expected_dynamodb_response}
        mock_dynamodb.Table.return_value.put_item.return_value = {'Item': expected_dynamodb_response}
        
        result = post_complexity_analyzer_results.lambda_handler(event, context)
        self.assertEqual(result, {"statusCode": 200, "body": "Input code passed security check"})
