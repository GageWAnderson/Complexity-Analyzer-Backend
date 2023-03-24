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

# TODO: Make an enumeration of allowed arg type strings in a Lambda Layer
# TODO: Inform the API caller about the allowed arg types and their formatting
allowed_arg_types = ['int', 'string', 'list<string>', 'list<int>']


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def lambda_handler(event, context):

    try:
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
    if validate_code_security(body_json['inputCode'], body_json['args']):
        try:
            logger.debug('Calling complexity analyzer...')
            call_complexity_analyzer(
                body_json['inputCode'], body_json['args'], user_id)
            return construct_response(codes.ok, 'Input code passed security check')
        except Exception as e:
            return construct_response(codes.bad_request, 'Failed to call complexity analyzer', str(e))
    else:
        return construct_response(codes.bad_request, 'Input code failed security check, warning: this may be a malicious request')


def validate_code_security(code, args):
    response = lambdaClient.invoke(
        FunctionName='code_security_validator',
        InvocationType='RequestResponse',
        Payload=json.dumps({'args': args, 'inputCode': code})
    ).get('Payload').read().decode('utf-8')

    logger.debug(f'Code security validation response: {response}')

    return json.loads(response)['statusCode'] == codes.ok


def call_complexity_analyzer(code, args, user_id):
    lambdaClient.invoke(
        FunctionName='code_complexity_analyzer',
        InvocationType='Event',
        Payload=json.dumps(
            {'inputCode': code, 'args': args, 'user-id': user_id})
    )


def validate_all_arguments(json):
    number_of_variable_args = 0
    for arg in json['args']:
        response, isVariable = validate_argument(arg)
        if response:
            return response
        if isVariable: # Only 1 variable argument per call is allowed
            number_of_variable_args += 1
        if number_of_variable_args > max_number_of_variable_args:
            return construct_response(codes.bad_request, 'Too many variable arguments')

    if number_of_variable_args < min_number_of_variable_args:
        # One arg must be variable, otherwise there's nothing to do
        return construct_response(codes.bad_request, 'Too few variable arguments')
    else:
        return None


def validate_argument(argJsonObject):
    if 'argName' not in argJsonObject or not argJsonObject['argName']:
        return construct_response(codes.bad_request, 'Missing argument name field'), False
    elif not str.isidentifier(argJsonObject['argName']):
        return construct_response(codes.bad_request, 'Invalid argument name'), False
    elif 'argType' not in argJsonObject:
        return construct_response(codes.bad_request, 'Missing argument type field'), False
    elif argJsonObject['argType'] not in allowed_arg_types:
        return construct_response(codes.bad_request, 'Invalid argument type'), False
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
