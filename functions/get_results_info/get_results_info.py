import json
import boto3
from requests import codes

s3client = boto3.client('s3')

user_results_s3_bucket = 'complexity-analyzer-results-test'


def lambda_handler(event, context):

    try:
        user_id = event['user-id']
    except Exception as e:
        return construct_response(codes.bad_request, f'Invalid user ID header: {str(e)}')

    try:
        results = query_user_results(user_id)
        # TODO: Modify response to contain results with user results metadata
        return construct_response(codes.ok, body=json.dumps(results))
    except Exception as e:
        return construct_response(codes.bad_request, error=f'Error querying user results: {str(e)}')


def construct_response(status_code, body=None, error=None):
    if error:
        response = {
            'statusCode': status_code,
            'body': json.dumps({'error': error})
        }
    else:
        response = {
            'statusCode': status_code,
            'body': json.dumps({'message': body})
        }
    return response


def query_user_results(user_id):
    # Define the parameters for the query
    params = {
        'Bucket': user_results_s3_bucket,
        'Prefix': user_id
    }

    # Query the S3 bucket
    response = s3client.list_objects_v2(**params)

    return response
