import json
import boto3
import logging
from requests import codes

s3 = boto3.resource('s3')

user_results_s3_bucket = 'complexity-analyzer-results-test'

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def lambda_handler(event, context):

    try:
        user_id = event['params']['header']['user-id']
    except Exception as e:
        return construct_response(codes.bad_request, f'Invalid user ID header: {str(e)}')

    try:
        results = query_user_results_metadata(user_id)
        if not results:
            return construct_response(codes.not_found, f'No results found for user {user_id}')
        else:
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
            'body': json.dumps({'user-metadata': body})
        }
    return response


def query_user_results_metadata(user_id):
    result = []
    bucket = s3.Bucket(user_results_s3_bucket)
    logger.debug(
        f'Getting user metadata objects from bucket {user_results_s3_bucket}')
    for obj in bucket.objects.filter(Prefix=user_id):
        logger.debug(f'Object key: {obj.key}')
        if obj.key.endswith('metadata.json'):
            logger.debug(f'Getting metadata object: {obj.key}')
            metadata_object = s3.Object(user_results_s3_bucket, obj.key)
            metadata = json.loads(metadata_object.get()['Body'].read())
            result.append(metadata)
    return result
