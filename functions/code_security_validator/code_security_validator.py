import json
from requests import codes
import RestrictedPython
import ast
import logging

# Define a dictionary of safe Python built-in functions and modules
safe_builtins = {
    '__builtins__': {
        'range': range,
        'len': len,
        'abs': abs,
        'float': float,
        'int': int,
        'str': str,
        'list': list,
        'dict': dict,
        'tuple': tuple,
        'set': set,
        'bool': bool,
    },
}

restricted_globals = {'ast': ast}
restricted_locals = {}

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def lambda_handler(event, context):

    try:
        input_code = event['inputCode']
    except Exception as e:
        return construct_response(codes.bad_request, f'Failed to process input code: {str(e)}')

    try:
        logger.debug(f'Compiling input code in restricted envionment: {input_code}')
        restricted_code = RestrictedPython.compile_restricted(
            f'ast.parse({input_code}))')
        logger.debug(f'Input code compiled successfully: {restricted_code}')
    except Exception as e:
        return construct_response(codes.bad_request, f'Failed to compile input code in restricted envionment, warning this code might be malicious.: {str(e)}')

    return construct_response(codes.ok, 'Input code passed security check')


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
