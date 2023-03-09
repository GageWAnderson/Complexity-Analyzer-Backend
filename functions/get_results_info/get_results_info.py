import json
import boto3
import logging
from requests import codes

s3 = boto3.resource('s3')

user_results_s3_bucket = 'complexity-analyzer-results-test'

logger = logging.getLogger()
logger.setLevel(logging.ERROR)


def lambda_handler(event, context):

    try:
        user_id = event['params']['header']['user-id']
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
    bucket = s3.Bucket(user_results_s3_bucket)
    objects = bucket.objects.filter(Prefix=user_id)

    if len(objects) > 0 and objects[0].key == user_id:
        # TODO: Modify the return statement to match the data structure of the user results
        return f'User {user_id} successfully queried'
    else:
        return None
