import json
import boto3
from requests import codes
import logging
import time

s3 = boto3.resource('s3')
bucket_name = 'complexity-analyzer-results-test'

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def lambda_handler(event, context):

    try:
        inputCode = event['inputCode']
        args = event['args']
        complexity = event['complexity']
        user_id = event['user-id']
        logger.debug(
            f'Input code: {inputCode}, args: {args}, complexity: {complexity}, user-id: {user_id}')
        post_to_s3(inputCode, args, complexity, user_id)
    except Exception as e:
        return {
            'statusCode': codes.bad_request,
            'body': json.dumps({'message': 'Bad request'})
        }


def post_to_s3(inputCode, args, complexity, user_id):
    bucket = s3.Bucket(bucket_name)
    prefix_objs = list(bucket.objects.filter(Prefix=f'{user_id}/'))
    prefix_exists = len(prefix_objs) > 0

    if not prefix_exists:
        bucket.put_object(Key=f'{user_id}/')

    timestamp = str(int(time.time()))
    object_key = f'{user_id}/{timestamp}.json'

    s3_object = s3.Object(bucket_name, object_key)
    logger.debug(f'Writing to s3 object: {s3_object}')
    s3_object.put(Body=json.dumps({
        'inputCode': inputCode,
        'args': args,
        'complexity': complexity,
        'user-id': user_id
    }))
