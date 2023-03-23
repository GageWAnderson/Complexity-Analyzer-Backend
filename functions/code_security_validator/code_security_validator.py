import json
from requests import codes
from RestrictedPython import safe_builtins, compile_restricted_function
import ast
import logging
import threading

restricted_function_name = 'restricted_function_name'

safe_locals = {}
safe_globals = {'ast': ast, '__builtins__': safe_builtins, '_getiter_': iter}

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

default_int_arg_value = 0
default_string_arg_value = ''

# TODO: Think Harder about what this should be
input_code_timeout_seconds = 5.0


def lambda_handler(event, context):

    try:
        input_function_body = event['inputCode']
        args = event['args']
        logger.debug(f'Input code: {input_function_body}')
    except Exception as e:
        return construct_response(codes.bad_request, f'Failed to process input code: {str(e)}')

    try:
        logger.debug('Compiling input code in restricted envionment')
        compiled_function = compile_restricted_function(
            parseArgsToCommaDelimitedList(args), input_function_body, restricted_function_name)

        # TODO: Handle compilation errors inside the compiled_function object
        logger.debug(str(compiled_function))

        if str(compiled_function.errors) != '()':
            return construct_response(codes.bad_request, f'Failed to compile input code in restricted envionment, warning this code might be malicious.: {str(compiled_function.errors)}')

        exec(compiled_function.code, safe_globals, safe_locals)
        compiled_function = safe_locals[restricted_function_name]

        runCompiledFunctionWithDefaultArgs(
            compiled_function, getDefaultArgs(args))
    except Exception as e:
        return construct_response(codes.bad_request, f'Failed to compile and run input code in restricted envionment, warning this code might be malicious.: {str(e)}')

    return construct_response(codes.ok, 'Input code passed security check')


def runCompiledFunctionWithDefaultArgs(compiled_function, default_args):
    def timeout_handler():
        raise Exception('Timeout')

    timer = threading.Timer(input_code_timeout_seconds, timeout_handler)
    timer.start()

    try:
        result = compiled_function(*default_args)
    except:
        raise Exception('Timeout')

    timer.cancel()

    return result


def parseArgsToCommaDelimitedList(args):
    logger.debug(f'Parsing args to comma delimited list: {args}')
    result = []
    for arg in args:
        result.append(arg['argName'])
    logger.debug(f'Parsed args to comma delimited list: {",".join(result)}')
    return ','.join(result)


def getDefaultArgs(args):
    result = []
    # TODO: Add an enumeration in the lambda layer of allowed argument types
    # TODO: Add more argument types
    for arg in args:
        if arg['argType'] == 'int':
            result.append(default_int_arg_value)
        elif arg['argType'] == 'string':
            result.append(default_string_arg_value)
    return result


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
