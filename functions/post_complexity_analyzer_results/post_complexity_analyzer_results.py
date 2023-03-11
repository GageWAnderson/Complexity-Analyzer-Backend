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
        complexity_graph = event['complexity-graph']
        logger.debug(
            f'Input code: {inputCode}, args: {args}, complexity: {complexity}, user-id: {user_id}')
        post_to_s3(inputCode, args, complexity, complexity_graph, user_id)
    except Exception as e:
        return {
            'statusCode': codes.bad_request,
            'body': json.dumps({'message': 'Bad request'})
        }


def post_to_s3(inputCode, args, complexity, complexity_graph, user_id):

    # Timestamps are unique, so we can use them as keys
    timestamp = str(int(time.time()))
    prefix = f'{user_id}/{timestamp}'
    logger.debug(f'Prefix: {prefix}')

    metadata_object_key = f'{prefix}/metadata.json'
    logger.debug(f'Object key: {metadata_object_key}')

    s3_metadata_object = s3.Object(bucket_name, metadata_object_key)
    logger.debug(f'Writing to s3 object: {s3_metadata_object}')
    s3_metadata_object.put(Body=json.dumps({
        'inputCode': inputCode,
        'args': args,
        'complexity': complexity,
        'user-id': user_id
    }))

    complexity_graph_object_key = f'{prefix}/graph.csv'
    logger.debug(f'Object key: {complexity_graph_object_key}')
    s3_graph_object = s3.Object(bucket_name, complexity_graph_object_key)
    logger.debug(f'Writing to s3 object: {s3_graph_object}')
    s3_graph_object.put(Body=complexity_graph)
