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
        if not results or len(results) == 0:
            return construct_response(codes.not_found, f'No results found for user {user_id}')
        else:
            return construct_response(codes.ok, body=results)
    except Exception as e:
        return construct_response(codes.internal_server_error, error=f'Error querying user results: {str(e)}')


def get_result_graph_as_json(user_id, timestamp):
    graph_object = f'{user_id}/{timestamp}/graph.csv'

    try:
        csv_graph = s3.Object(user_results_s3_bucket, graph_object)
        csv_file = csv_graph.get()['Body'].read().decode('utf-8')
        logger.debug(f'CSV file: {csv_file}')
        csv_reader = csv.DictReader(csv_file)
        return [row for row in csv_reader]
    except Exception as e:
        logger.error(f'Error getting graph object: {str(e)}')
        raise e


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
