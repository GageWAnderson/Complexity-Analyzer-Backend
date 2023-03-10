import json
import boto3
from requests import codes

s3client = boto3.client('s3')

def lambda_handler(event, context):

    try:
        inputCode = event['inputCode']
        args = event['args']
        complexity = event['complexity']
        user_id = event['user-id']
        post_to_s3(inputCode, args, complexity, user_id)
    except Exception as e:
        return {
            'statusCode': codes.bad_request,
            'body': json.dumps({'message': 'Bad request'})
        }

def post_to_s3(inputCode, args, complexity, user_id):
    s3client.put_object(
        Bucket='code-complexity-analyzer-results',
        Key='results.json',
        Body=json.dumps({
            'inputCode': inputCode,
            'args': args,
            'complexity': complexity,
            'user-id': user_id
        })
    )