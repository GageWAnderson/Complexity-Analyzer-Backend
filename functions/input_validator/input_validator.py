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

MAX_INPUT_SIZE_LIMIT = 1000000

lambdaClient = boto3.client("lambda")
client = boto3.client("cognito-idp")

# TODO: Make an enumeration of allowed arg type strings in a Lambda Layer
# TODO: Inform the API caller about the allowed arg types and their formatting
allowed_arg_types = ["int", "string", "list<string>", "list<int>"]


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def lambda_handler(event, context):
    try:
        request_body = json.loads(event["body"])
    except Exception as e:
        return construct_response(codes.bad_request, "Invalid JSON body", str(e))

    try:
        uuid = event["queryStringParameters"]["uuid"]
    except Exception as e:
        return construct_response(
            codes.bad_request, "Unable to get UUID from request", str(e)
        )

    if "inputCode" not in request_body:
        return construct_response(codes.bad_request, "Missing input code field")
    elif (
        "inputCode" in request_body and len(request_body["inputCode"]) > max_code_length
    ):
        return construct_response(codes.bad_request, "Input code too long")
    elif "args" not in request_body:
        return construct_response(codes.bad_request, "Missing arguments field")
    elif (
        "args" in request_body
        and len(request_body["args"]) > max_args_number
        or len(request_body["args"]) < min_args_number
    ):
        return construct_response(codes.bad_request, "Invalid argument number")
    elif "maxInputSize" not in request_body:
        return construct_response(codes.bad_request, "Missing max input size field")
    elif not isValidMaxInputSize(request_body["maxInputSize"]):
        return construct_response(codes.bad_request, "Invalid max input size")
    else:
        response = validate_all_arguments(request_body)
        if response:
            return response

    logger.debug("Validating input code...")
    if validate_code_security(request_body["inputCode"], request_body["args"]):
        try:
            logger.debug("Calling complexity analyzer...")
            call_complexity_analyzer(
                request_body["inputCode"],
                request_body["args"],
                request_body["maxInputSize"],
                uuid,
            )
            return construct_response(codes.ok, "Input code passed security check")
        except Exception as e:
            return construct_response(
                codes.bad_request, "Failed to call complexity analyzer", str(e)
            )
    else:
        return construct_response(
            codes.bad_request,
            "Input code failed security check, warning: this may be a malicious request",
        )


def validate_code_security(code, args):
    response = (
        lambdaClient.invoke(
            FunctionName="code_security_validator",
            InvocationType="RequestResponse",
            Payload=json.dumps({"args": args, "inputCode": code}),
        )
        .get("Payload")
        .read()
        .decode("utf-8")
    )

    logger.debug(f"Code security validation response: {response}")

    return json.loads(response)["statusCode"] == codes.ok


def call_complexity_analyzer(code, args, maxInputSize, user_id):
    lambdaClient.invoke(
        FunctionName="code_complexity_analyzer",
        InvocationType="Event",
        Payload=json.dumps(
            {
                "inputCode": code,
                "args": args,
                "maxInputSize": maxInputSize,
                "user-id": user_id,
            }
        ),
    )


def validate_all_arguments(json):
    number_of_variable_args = 0
    for arg in json["args"]:
        response, isVariable = validate_argument(arg)
        if response:
            return response
        if isVariable:  # Only 1 variable argument per call is allowed
            number_of_variable_args += 1
        if number_of_variable_args > max_number_of_variable_args:
            return construct_response(codes.bad_request, "Too many variable arguments")

    if number_of_variable_args < min_number_of_variable_args:
        # One arg must be variable, otherwise there's nothing to do
        return construct_response(codes.bad_request, "Too few variable arguments")
    else:
        return None


def validate_argument(argJsonObject):
    if "argName" not in argJsonObject or not argJsonObject["argName"]:
        return (
            construct_response(codes.bad_request, "Missing argument name field"),
            False,
        )
    elif not str.isidentifier(argJsonObject["argName"]):
        return construct_response(codes.bad_request, "Invalid argument name"), False
    elif "argType" not in argJsonObject:
        return (
            construct_response(codes.bad_request, "Missing argument type field"),
            False,
        )
    elif argJsonObject["argType"] not in allowed_arg_types:
        return construct_response(codes.bad_request, "Invalid argument type"), False
    elif "variable" not in argJsonObject:
        return construct_response(codes.bad_request, "Missing variable field"), False
    elif len(argJsonObject) != number_of_arg_fields:
        return construct_response(codes.bad_request, "Invalid argument object"), False
    else:
        if argJsonObject["variable"]:
            return None, True
        else:
            return None, False


def isValidMaxInputSize(maxInputSize):
    return (
        isinstance(maxInputSize, int)
        and maxInputSize > 0
        and maxInputSize <= MAX_INPUT_SIZE_LIMIT
    )


def construct_response(status_code, body=None, error=None):
    body = None
    if error:
        body = {"error": error}
    else:
        body = {"message": body}

    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": body,
    }
