import string
import threading
import time
from requests import codes
import json
import boto3
import logging
from RestrictedPython import safe_builtins, compile_restricted_function
import ast
import numpy as np
import random
import traceback

lambdaClient = boto3.client('lambda')

safe_locals = {}
safe_globals = {'ast': ast, '__builtins__': safe_builtins, '_getiter_': iter}

# TODO: Think Harder about what this should be
max_int_size = 10000
default_max_input_size = 1000

number_of_steps = 100

max_polynomial_degree = 3
max_exp_base = 3

default_int_value = 10
default_string_value = "Hello World"
default_list_of_ints_value = [1]
default_list_of_strings_value = ["a"]

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

restricted_function_name = 'restricted_function'

# Defines the timeout for 1 run of the input code
# input_code_timeout_seconds * number_of_steps < function timeout
input_code_timeout_seconds = 60 * 10  # Lambda handles overall timeout


def lambda_handler(event, context):
    try:
        input_function_body = event['inputCode']
        args = event['args']
        maxInputSize = event['maxInputSize']
        user_id = event['user-id']

        compiled_function = compile_input_function_restricted(
            input_function_body, parseArgsToCommaDelimitedList(args))

        logger.debug(f'Running code with variable input: {args}')
        runtime_graph = run_code_with_variable_input(
            compiled_function, args, maxInputSize)

        logger.debug(f'runtime_graph: {runtime_graph}')

        complexity = get_complexity_from_runtime_graph(runtime_graph)

        publish_results(input_function_body, args,
                        complexity, runtime_graph, user_id)

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
        logger.debug(
            "Failed to compile input code in restricted envionment, warning this code might be malicious.")
        raise e


def run_code_with_variable_input(compiled_function, args, maxInputSize=default_max_input_size):
    runtime_graph = []
    variable_arg, variable_arg_type = getVariableArg(args)
    arg_range = [0, maxInputSize]
    step_size = getStepSize(arg_range)

    logger.debug(f'arg_range: {arg_range}, step_size: {step_size}')
    for i in range(number_of_steps):
        variable_arg_value = getArgValue(
            variable_arg_type, arg_range, step_size, i)
        args_for_this_run = getArgsForThisRun(args, variable_arg_value)
        try:
            runtime = run_and_time_code_execution(
                compiled_function, args_for_this_run)
            runtime_graph.append((variable_arg_value, runtime))
        except Exception as e:
            # Some inputs may fail, don't stop the whole execution since others may succeed
            logger.debug(
                f'Failed to run code with variable input: Args: {args_for_this_run}, Exception: {str(e)}')

    return runtime_graph


def run_and_time_code_execution(compiled_function, args):
    def timeout_handler():
        raise TimeoutError()

    timer = threading.Timer(input_code_timeout_seconds, timeout_handler)
    timer.start()

    try:
        start_time = time.time()
        compiled_function(*args)
    except TimeoutError as e1:
        logger.debug('Code execution timed out')
        raise e1
    except Exception as e2:
        logger.debug(f'Code execution failed: {str(e2)}')
        raise e2

    timer.cancel()

    end_time = time.time()
    return end_time - start_time


def get_complexity_from_runtime_graph(runtime_graph):
    try:

        logger.debug(
            f'Calculating complexity from runtime graph: {runtime_graph}')
        points = np.array(runtime_graph)
        x_axis = points[:, 0]
        y_axis = points[:, 1]

        # Find the Polynomial that fits the data
        polynomial_best_error, best_coefficients = find_best_polyfit(
            x_axis, y_axis, max_polynomial_degree)
        polynomial_complexity = len(best_coefficients) - 1

        log_best_error = log_squared_error(x_axis, y_axis)

        nlogn_best_error = nlogn_squared_error(x_axis, y_axis)

        exp_best_error, exp_best_base = exp_squared_error(
            x_axis, y_axis, max_exp_base)

        factorial_squared_error = factorial_squared_error(x_axis, y_axis)

        # TODO: MVP+ Support non-polynomial complexity
        return format_complexity(polynomial_best_error, polynomial_complexity, log_best_error, nlogn_best_error, exp_best_error, exp_best_base, factorial_squared_error)
    except Exception as e:
        logger.debug(
            f'Failed to calculate complexity from runtime graph: {traceback.format_exc()}')
        raise e


def find_best_polyfit(x, y, n):
    try:
        best_coefficients = None
        best_error = float('inf')
        # Degree 0 = Constant, Degree 1 = Linear, etc.
        for degree in range(n+1):
            coefficients = np.polyfit(x, y, degree)
            fit = np.polyval(coefficients, x)
            error = np.sum((fit - y)**2)
            if error < best_error:
                best_coefficients = coefficients
                best_error = error
        logger.debug(
            f'Best error: {best_error}, Best coefficients: {best_coefficients}')
        return best_error, best_coefficients
    except Exception as e:
        logger.debug(f'Failed to find best polyfit: {traceback.format_exc()}')
        raise e


def log_squared_error(x, y):
    try:
        x_axis_no_zeros, y_axis_no_zeros = remove_zero_points_x_y(x, y)
        log_x = np.log(x_axis_no_zeros)
        A = np.vstack([log_x, np.ones(len(log_x))]).T
        m, c = np.linalg.lstsq(A, y_axis_no_zeros, rcond=None)[0]
        y_fit = m*log_x + c
        error = np.sum((y_axis_no_zeros - y_fit)**2)
        logger.debug(f'Log squared error: {error}')
        return error
    except Exception as e:
        logger.debug(
            f'Failed to calculate log squared error: {traceback.format_exc()}')
        raise e


def nlogn_squared_error(x, y):
    try:
        x_axis_no_zeros, y_axis_no_zeros = remove_zero_points_x_y(x, y)
        nlogn = (x_axis_no_zeros) * np.log(x_axis_no_zeros)
        A = np.vstack([nlogn, np.ones(len(nlogn))]).T
        m, c = np.linalg.lstsq(A, y_axis_no_zeros, rcond=None)[0]
        y_fit = m*nlogn + c
        error = np.sum((y_axis_no_zeros - y_fit)**2)
        logger.debug(f'NlogN squared error: {error}')
        return error
    except Exception as e:
        logger.debug(
            f'Failed to calculate nlogn squared error: {traceback.format_exc()}')
        raise e


# def exp_squared_error(x, y, max_base):

#     def safe_exp(base, x):
#         res = []
#         with np.errstate(over='ignore'):
#             res = np.power(base, x)

#         x_value_no_inf_or_nan = []
#         y_value_no_corresponding_nan_or_inf = []
#         for i in range(len(res)):
#             if not (res[i] == None or res[i] == np.inf or res[i] == -np.inf or np.isnan(res[i])):
#                 x_value_no_inf_or_nan.append(x[i])
#                 y_value_no_corresponding_nan_or_inf.append(y[i])

#         return x_value_no_inf_or_nan, y_value_no_corresponding_nan_or_inf

#     best_error = float('inf')
#     best_base = None
#     for exp_base in range(2, max_base):
#         exp_x_no_inf, y_values_no_corresponding_inf = safe_exp(exp_base, x)
#         A = np.vstack([exp_x_no_inf, np.ones(len(exp_x_no_inf))]).T
#         m, c = np.linalg.lstsq(A, y_values_no_corresponding_inf, rcond=None)[0]
#         y_fit = m*exp_x_no_inf + c
#         error = np.sum((y_values_no_corresponding_inf - y_fit)**2)
#         if error < best_error:
#             best_error = error
#             best_base = exp_base
#     return best_error, best_base


def factorial_squared_error(x, y):
    fact_x = np.factorial(x)
    A = np.vstack([fact_x, np.ones(len(fact_x))]).T
    m, c = np.linalg.lstsq(A, y, rcond=None)[0]
    y_fit = m*fact_x + c
    error = np.sum((y - y_fit)**2)
    return error


def format_complexity(polynomial_best_error, polynomial_complexity, log_best_error, nlogn_best_error, exp_best_error, exp_base, factorial_best_error):
    best_error = min(polynomial_best_error, log_best_error,
                     nlogn_best_error, exp_best_error, factorial_best_error)
    if polynomial_best_error == best_error:
        if polynomial_complexity == 0:
            return 'O(1)'
        elif polynomial_complexity == 1:
            return 'O(n)'
        else:
            return f'O(n^{polynomial_complexity})'
    elif log_best_error == best_error:
        return 'O(log(n))'
    elif nlogn_best_error == best_error:
        return 'O(nlog(n))'
    elif exp_best_error == best_error:
        return f'O({exp_base}^n)'
    elif factorial_best_error == best_error:
        return 'O(n!)'
    else:
        raise Exception('No best fit found')


def publish_results(inputCode, args, complexity, complexity_graph, user_id):
    try:
        logger.debug(
            f'Publishing results to post_complexity_analyzer_results (user_id: {user_id}')
        lambdaClient.invoke(
            FunctionName='post_complexity_analyzer_results',
            InvocationType='Event',
            Payload=json.dumps({
                'inputCode': inputCode,
                'args': args,
                'complexity': complexity,
                'complexity-graph': complexity_graph,
                'user-id': user_id
            })
        )
    except Exception as e:
        logger.debug(f'Failed to publish results: {traceback.format_exc()}')
        raise e


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


def getStepSize(arg_range):
    return (arg_range[1] - arg_range[0]) // number_of_steps


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
            elif arg['argType'] == 'list<int>':
                result.append(default_list_of_ints_value)
            elif arg['argType'] == 'list<string>':
                result.append(default_list_of_strings_value)
            else:
                raise Exception("Unsupported arg type")
    return result


def getArgValue(arg_type, arg_range, step_size, step_number):
    try:
        if arg_type == "int":
            return arg_range[0] + (step_size * step_number)
        elif arg_type == "string":
            res = ""
            for _ in range(arg_range[0] + (step_size * step_number)):
                res += random.choice(string.ascii_lowercase)
            return res
        elif arg_type == "list<int>":
            res = []
            for _ in range(arg_range[0] + (step_size * step_number)):
                res.append(random.randint(0, max_int_size))
            return res
        elif arg_type == "list<string>":
            res = []
            for _ in range(arg_range[0] + (step_size * step_number)):
                res.append(random.choice(string.ascii_lowercase))
            return res
    except Exception as e:
        logger.debug(f'Failed to get arg value: {traceback.format_exc()}')
        raise e


def getVariableArg(args):
    for arg in args:
        if arg['variable']:
            return arg, arg['argType']
    raise Exception("No variable arg found")


def remove_zero_points_x_y(x, y):
    x_result = []
    y_result = []
    for i in range(len(x)):
        if x[i] != 0:
            x_result.append(x[i])
            y_result.append(y[i])
    return x_result, y_result
