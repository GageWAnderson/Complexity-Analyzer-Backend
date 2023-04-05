import boto3
import json
import traceback
from requests import codes
import logging

api_gateway_client = boto3.client("apigateway")
dynamodb_client = boto3.resource("dynamodb")

api_keys_table_name = "complexity-analyzer-api-keys"

api_gateway_stage = "Prod"
api_gateway_id = "xa51s0jinb"

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def lambda_handler(event, context):
    try:
        uuid = event["queryStringParameters"]["uuid"]
    except Exception as e:
        logger.error(traceback.format_exc())
        return construct_response(codes.bad_request, error="Missing UUID")

    try:
        api_key = get_api_key(uuid)
        if not api_key:
            api_key = create_api_key(uuid)
        return construct_response(codes.ok, body=api_key)
    except Exception as e:
        logger.error(traceback.format_exc())
        return construct_response(codes.bad_request, error="Error getting API Key")


def get_api_key(uuid):
    # fmt: off
    api_key = dynamodb_client.Table(api_keys_table_name).get_item(Key={"uuid": uuid})
    # fmt: on
    if "Item" in api_key:
        return api_key["Item"]["apiKey"]
    else:
        return None


def create_api_key(uuid):
    api_key = api_gateway_client.create_api_key()
    logger.debug(f"API Key ID: {api_key['id']}")
    # fmt: off
    dynamodb_client.Table(api_keys_table_name).put_item(Item={"uuid": uuid, "apiKey": api_key["id"]})
    # fmt: on
    return api_key


def construct_response(status_code, body=None, error=None):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps({"body": body, "error": error}),
    }
