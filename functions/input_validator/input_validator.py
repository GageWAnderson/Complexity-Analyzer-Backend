import json
import boto3

http_success_response_code = 200


def lambda_handler(event, context):
    return {
        'statusCode': 200,
        'body': construct_return_json(http_success_response_code, event['body'])
    }


def construct_return_json(status, message):
    return {
        'statusCode': status,
        'body': json.dumps(message)
    }
