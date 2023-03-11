from requests import codes
import json
import boto3
import logging

lambdaClient = boto3.client('lambda')

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def lambda_handler(event, context):
    try:
        inputCode = event['inputCode']
        args = event['args']
        user_id = event['user-id']

        logger.debug(
            f'Input code: {inputCode}, args: {args}, user-id: {user_id}')

        publish_results(inputCode, args, 'placeholder', 'placeholder', user_id)

        return construct_response(codes.ok, 'Called Code Complexity Analyzer')
    except Exception as e:
        return construct_response(codes.bad_request, 'Failed to publish results', str(e))


def publish_results(inputCode, args, complexity, complexity_graph, user_id):
    lambdaClient.invoke_async(
        FunctionName='post_complexity_analyzer_results',
        InvokeArgs=json.dumps({
            'inputCode': inputCode,
            'args': args,
            'complexity': complexity,
            'complexity-graph': complexity_graph,
            'user-id': user_id
        })
    )


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
