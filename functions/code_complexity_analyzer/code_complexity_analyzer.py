import threading
import time
from requests import codes
import json
import boto3
import logging
from RestrictedPython import safe_builtins, compile_restricted_function
import ast

lambdaClient = boto3.client('lambda')

safe_locals = {}
safe_globals = {'ast': ast, '__builtins__': safe_builtins, '_getiter_': iter}

# TODO: Think Harder about what this should be
max_int_size = 1000000000
max_string_length = 1000
number_of_steps = 10

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

restricted_function_name = 'restricted_function'

# Defines the timeout for 1 run of the input code
input_code_timeout_seconds = 1


def lambda_handler(event, context):
    try:
        input_function_body = event['inputCode']
        args = event['args']
        user_id = event['user-id']

        compiled_function = compile_input_function_restricted(input_function_body, parseArgsToCommaDelimitedList(args))

        logger.debug(f'Running code with variable input: {args}')
        runtime_graph = run_code_with_variable_input(compiled_function, args)

        logger.debug(f'runtime_graph: {runtime_graph}')

        complexity = get_complexity_from_runtime_graph(runtime_graph)

        publish_results(input_function_body, args, complexity, runtime_graph, user_id)

        return construct_response(codes.ok, 'Called Code Complexity Analyzer')
    except Exception as e:
        return construct_response(codes.bad_request, 'Failed to publish results', str(e))


def compile_input_function_restricted(input_function_body, args):
    try:
        logger.debug('Compiling input code in restricted envionment')
        compiled_function = compile_restricted_function(
            args, input_function_body, restricted_function_name)

        # TODO: Handle compilation errors inside the compiled_function object
        logger.debug(str(compiled_function))

        if str(compiled_function.errors) != '()':
            return construct_response(codes.bad_request, f'Failed to compile input code in restricted envionment, warning this code might be malicious.: {str(compiled_function.errors)}')

        exec(compiled_function.code, safe_globals, safe_locals)
        return safe_locals[restricted_function_name]
    except Exception as e:
        logger.debug("Failed to compile input code in restricted envionment, warning this code might be malicious.")
        raise e

def run_code_with_variable_input(compiled_function, args):
    runtime_graph = []
    arg_range = getArgRange(getVariableArg(args))
    step_size = getStepSize(arg_range) # TODO: How many steps can I do before timeout?

    logger.debug(f'arg_range: {arg_range}, step_size: {step_size}')
    for i in range(number_of_steps):
        variable_arg_value = getArgValue(arg_range, step_size, i)
        args_for_this_run = getArgsForThisRun(args, variable_arg_value)
        logger.debug(f'i: {i}, Running code with args: {args_for_this_run} (variable arg value: {variable_arg_value})')
        try:
            runtime = run_and_time_code_execution(compiled_function, args_for_this_run)
            logger.debug(f'Code execution took {runtime} seconds')
        except Exception as e:
            # Some inputs may fail, don't stop the whole execution since others may succeed
            logger.debug(f'Code execution failed, skipping this entry in the graph: {e}')
        else:
            runtime_graph.append((variable_arg_value, runtime))
    
    return runtime_graph

def run_and_time_code_execution(compiled_function, args):
    def timeout_handler():
        raise Exception('Timeout')

    timer = threading.Timer(input_code_timeout_seconds, timeout_handler)
    timer.start()

    try:
        start_time = time.time()
        compiled_function(*args)
    except Exception as e:
        raise e
    finally:
        timer.cancel()
    
    end_time = time.time()
    return end_time - start_time

def get_complexity_from_runtime_graph(runtime_graph):
    return "O(n)" # TODO: Calculate complexity from runtime graph

def publish_results(inputCode, args, complexity, complexity_graph, user_id):
    lambdaClient.invoke(
        FunctionName='post_complexity_analyzer_results',
        InvocationType='RequestResponse',
        InvokeArgs=json.dumps({
            'inputCode': inputCode,
            'args': args,
            'complexity': complexity,
            'complexity-graph': complexity_graph,
            'user-id': user_id
        })
    )

def parseArgsToCommaDelimitedList(args):
    logger.debug(f'Parsing args to comma delimited list: {args}')
    result = []
    for arg in args:
        result.append(arg['argName'])
    logger.debug(f'Parsed args to comma delimited list: {",".join(result)}')
    return ','.join(result)

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

def getArgRange(variableArg):
    if variableArg["argType"] == "int":
        return [0, max_int_size] # Vary Int Size
    elif variableArg["argType"] == "string":
        return [0, max_string_length] # Vary Length of input String
    else:
        # TODO: Use the enumeration of argTypes in the Lambda Layer
        raise Exception("Unsupported variable arg type")

def getStepSize(arg_range):
    return (arg_range[1] - arg_range[0]) / number_of_steps

default_int_value = 10
default_string_value = "Hello World"

def getArgsForThisRun(args, variable_arg_value):
    result = []
    for arg in args:
        if arg['variable']:
            result.append(variable_arg_value)
        else:
            # TODO: Update to use the enumeration of argTypes in the Lambda Layer
            if arg['argType'] == 'int':
                result.append(default_int_value)
            elif arg['argType'] == 'string':
                result.append(default_string_value)
            else:
                raise Exception("Unsupported arg type")
    return result

def getArgValue(arg_range, step_size, step_number):
    return arg_range[0] + (step_size * step_number)

def getVariableArg(args):
    for arg in args:
        if arg['variable']:
            return arg
    raise Exception("No variable arg found")