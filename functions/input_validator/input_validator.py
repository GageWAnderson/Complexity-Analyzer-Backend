import json
from requests import codes
import boto3
import logging

max_code_length = 500

min_args_number = 1
max_args_number = 3

min_number_of_variable_args = 1
max_number_of_variable_args = 1

number_of_arg_fields = 3

lambdaClient = boto3.client('lambda')


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def lambda_handler(event, context):

    try:
        # TODO: Do we need this here since we can call in in the Code Complexity Analyzer Lambda Function?
        user_id = event['params']['header']['user-id']
    except Exception as e:
        return construct_response(codes.bad_request, f'Invalid user ID header: {str(e)}')

    try:
        body_json = event['body-json']
    except Exception as e:
        return construct_response(codes.bad_request, 'Invalid JSON body', str(e))

    if 'inputCode' not in body_json:
        return construct_response(codes.bad_request, 'Missing input code field')
    elif 'inputCode' in body_json and len(body_json['inputCode']) > max_code_length:
        return construct_response(codes.bad_request, 'Input code too long')
    elif 'args' not in body_json:
        return construct_response(codes.bad_request, 'Missing arguments field')
    elif 'args' in body_json and len(body_json['args']) > max_args_number or len(body_json['args']) < min_args_number:
        return construct_response(codes.bad_request, 'Invalid argument number')
    else:
        response = validate_all_arguments(body_json)
        if response:
            return response

    logger.debug('Validating input code...')
    if validate_code_security(body_json['inputCode']):
        try:
            logger.debug('Calling complexity analyzer...')
            call_complexity_analyzer(body_json['inputCode'], body_json['args'], user_id)
            return construct_response(codes.ok, 'Input code passed security check')
        except Exception as e:
            return construct_response(codes.bad_request, 'Failed to call complexity analyzer', str(e))
    else:
        return construct_response(codes.bad_request, 'Input code failed security check, warning: this may be a malicious request')


def validate_code_security(code):
    response = lambdaClient.invoke(
        FunctionName='code_security_validator',
        InvocationType='RequestResponse',
        Payload=json.dumps({'inputCode': code})
    )

    return response['statusCode'] == codes.ok

def call_complexity_analyzer(code, args, user_id):
    lambdaClient.invoke_async(
        FunctionName='code_complexity_analyzer',
        InvokeArgs=json.dumps({'inputCode': code, 'args': args, 'user-id': user_id})
    )


def validate_all_arguments(json):
    number_of_variable_args = 0
    for arg in json['args']:
        response, isVariable = validate_argument(arg)
        if response:
            return response
        if isVariable:
            number_of_variable_args += 1
        if number_of_variable_args > max_number_of_variable_args:
            return construct_response(codes.bad_request, 'Too many variable arguments')

    if number_of_variable_args < min_number_of_variable_args:
        return construct_response(codes.bad_request, 'Too few variable arguments')
    else:
        return None


def validate_argument(argJsonObject):
    if 'argName' not in argJsonObject:
        return construct_response(codes.bad_request, 'Missing argument name field'), False
    elif 'argType' not in argJsonObject:
        return construct_response(codes.bad_request, 'Missing argument type field'), False
    elif 'variable' not in argJsonObject:
        return construct_response(codes.bad_request, 'Missing variable field'), False
    elif len(argJsonObject) != number_of_arg_fields:
        return construct_response(codes.bad_request, 'Invalid argument object'), False
    else:
        if argJsonObject['variable']:
            return None, True
        else:
            return None, False


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
