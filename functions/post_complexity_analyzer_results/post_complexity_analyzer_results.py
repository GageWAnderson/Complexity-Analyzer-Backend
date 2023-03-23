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
            f'Input code: {inputCode}, args: {args}, complexity: {complexity}, user-id: {user_id}, complexity-graph: {complexity_graph}')
        post_to_s3(inputCode, args, complexity, complexity_graph, user_id)
    except Exception as e:
        return {
            'statusCode': codes.internal_server_error,
            'body': json.dumps({'error': str(e)})
        }


def post_to_s3(inputCode, args, complexity, complexity_graph, user_id):

    # Timestamps are unique, so we can use them as keys
    timestamp = str(int(time.time()))
    prefix = f'{user_id}/{timestamp}'
    logger.debug(f'Prefix: {prefix}')

    bucket = s3.Bucket(bucket_name)
    prefix_in_bucket = list(bucket.objects.filter(Prefix=prefix))
    if len(prefix_in_bucket) > 0:
        logger.error(
            f'Prefix {prefix} already exists in bucket {bucket_name}')
        raise Exception(
            f'Prefix {prefix} already exists in bucket {bucket_name}')

    metadata_object_key = f'{prefix}/metadata.json'
    logger.debug(f'Object key: {metadata_object_key}')

    s3_metadata_object = s3.Object(bucket_name, metadata_object_key)
    logger.debug(f'Writing to s3 object: {s3_metadata_object}')
    s3_metadata_object.put(Body=json.dumps({
        'timestamp': timestamp,
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

    complexity_graph_object_key = f'{prefix}/graph.csv'
    s3.put_object(Bucket=bucket_name, Key=complexity_graph_object_key,
                  Body=parseToCsv(complexity_graph))
    logger.debug('Successfully wrote to s3 graph.csv object')
    

def parseToCsv(complexity_graph):
    result = ''
    for entry in complexity_graph:
        result += ','.join(str(entry[0]), str(entry[1])) + '\n'
    logger.debug(f'parseToCsv result: {str(result)}')
    return result
