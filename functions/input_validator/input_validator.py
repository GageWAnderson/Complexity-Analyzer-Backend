import json
import time
from requests import codes
import boto3
import logging

max_code_length = 500

min_args_number = 1
max_args_number = 3

lambdaClient = boto3.client('lambda')
logsClient = boto3.client('logs')

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):

    body = event['body']

    if not body:
        return construct_response(codes.bad_request, 'Empty request body')

    log_request_body(body, context)

    try:
        body_json = json.loads(body)
    except json.JSONDecodeError as e:
        return construct_response(codes.bad_request, 'Invalid JSON body', str(e))

    # Your validation logic here
    if 'inputCode' not in body_json:
        return construct_response(codes.bad_request, 'Missing input code field')
    elif 'inputCode' in body_json and len(body_json['inputCode']) > max_code_length:
        return construct_response(codes.bad_request, 'Input code too long')
    elif 'args' not in body_json:
        return construct_response(codes.bad_request, 'Missing arguments field')
    elif 'args' in body_json and len(body_json['args']) > max_args_number or len(body_json['args']) < min_args_number:
        return construct_response(codes.bad_request, 'Invalid argument number')
    else:
        for arg in body_json['args']:
            response = validate_argument(arg)
            if response:
                return response

    if validate_code_security(body_json['inputCode']):
        # Call Code Complexity Analyzer Lambda Function
        return construct_response(codes.ok, 'Request validated successfully')
    else:
        return construct_response(codes.bad_request, 'Input code failed security check, warning: this may be a malicious request')


def validate_code_security(code):
    return True
    # response = client.invoke(
    #     FunctionName='code_security_validator',
    #     InvocationType='RequestResponse',
    #     Payload=json.dumps({'inputCode': code})
    # )

    # if response['StatusCode'] == codes.ok:
    #     response_body = json.loads(response['Payload'].read())
    #     return response_body['message'] == 'Code security check passed'
    # else:
    #     return False


def validate_argument(argJsonObject):
    if 'argName' not in argJsonObject:
        return construct_response(codes.bad_request, 'Missing argument name field')
    elif 'argType' not in argJsonObject:
        return construct_response(codes.bad_request, 'Missing argument type field')
    elif 'variable' not in argJsonObject:
        return construct_response(codes.bad_request, 'Missing variable field')
    else:
        return None


def construct_response(status_code, message, error=None):
    return {
        'statusCode': status_code,
        'body': json.dumps({'message': message, 'error': error})
    }


def log_request_body(body, context):
    logger.info('Request body: ' + body)

    # Write the log message to CloudWatch Logs
    log_group_name = '/aws/lambda/{function_name}'.format(
        function_name=context.function_name)
    log_stream_name = context.aws_request_id
    logsClient.create_log_stream(
        logGroupName=log_group_name, logStreamName=log_stream_name)
    logsClient.put_log_events(logGroupName=log_group_name, logStreamName=log_stream_name, logEvents=[
        {
            'timestamp': int(round(time.time() * 1000)),
            'message': 'Request body: ' + body
        }
    ])
