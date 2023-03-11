import json
import logging
from requests import codes
import boto3
import csv

# This function gets the graph to display on the frontend, not to download

s3 = boto3.resource('s3')

user_results_s3_bucket = 'complexity-analyzer-results-test'

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def lambda_handler(event, context):
    try:
        user_id = event['params']['header']['user-id']
        timestamp = event['params']['header']['timestamp']
    except Exception as e:
        return construct_response(codes.bad_request, f'Invalid user ID header: {str(e)}')

    try:
        results = get_result_graph_as_json(user_id, timestamp)
        logger.debug(f'Graph results: {results}')
        if not results:
            return construct_response(codes.not_found, f'No results found for user {user_id}')
        else:
            return construct_response(codes.ok, body=json.dumps(results))
    except Exception as e:
        return construct_response(codes.internal_server_error, error=f'Error querying user results: {str(e)}')


def get_result_graph_as_json(user_id, timestamp):
    graph_object = f'{user_id}/{timestamp}/graph.csv'
    logger.debug(
        f'Getting user graph objects from bucket {user_results_s3_bucket}, graph_object: {graph_object}')

    try:
        csv_graph = s3.Object(user_results_s3_bucket, graph_object)
        csv_data = csv.DictReader(csv_graph.get()['Body'].read().decode('utf-8').splitlines())
        return list(csv_data)
    except Exception as e:
        logger.debug(f'Error getting graph object: {str(e)}')
        return None


def construct_response(status_code, body=None, error=None):
    if error:
        response = {
            'statusCode': status_code,
            'body': json.dumps({'error': error})
        }
    else:
        response = {
            'statusCode': status_code,
            'body': json.dumps({'results-graph': body})
        }
    return response
