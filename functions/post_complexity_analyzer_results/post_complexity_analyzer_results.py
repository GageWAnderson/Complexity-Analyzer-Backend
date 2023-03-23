from io import StringIO
import json
import boto3
from requests import codes
import logging
import time
import csv

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

    try:
        complexity_graph_object_key = f'{prefix}/graph.csv'
        graph_bytes = parseToCsv(complexity_graph)
        logger.debug(f'graph_bytes: {graph_bytes}')
        s3.put_object(Bucket=bucket_name, Key=complexity_graph_object_key,
                    Body=graph_bytes)
        logger.debug('Successfully wrote to s3 graph.csv object')
    except Exception as e:
        logger.error(f'Failed to write to s3 graph.csv object: {e}')
        raise e
    

def parseToCsv(complexity_graph):
    csv_data = StringIO()
    csv_writer = csv.writer(csv_data)
    csv_writer.writerows(complexity_graph)
    return csv_data.getvalue().encode('utf-8')
