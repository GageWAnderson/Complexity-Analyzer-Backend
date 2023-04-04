import json
import boto3
from boto3.dynamodb.conditions import Key
import logging
from requests import codes
import traceback

dynamodb = boto3.resource("dynamodb")
table_name = "complexity-analyzer-metadata-db"

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def lambda_handler(event, context):
    try:
        uuid = event["queryStringParameters"]["uuid"]
        logger.debug(f"Getting all metadata for uuid: {uuid}")
    except Exception as e:
        logger.error(f"Error getting UUID from request: {traceback.format_exc()}")
        return construct_response(
            codes.bad_request,
            error=f"Unable to get UUID from request",
        )

    try:
        results = get_all_metadata(uuid)
        if not results:
            return construct_response(
                codes.not_found, f"No results found for user {uuid}"
            )
        else:
            return construct_response(codes.ok, body=results)
    except Exception as e:
        logger.error(f"Error querying user results: {traceback.format_exc()}")
        return construct_response(
            codes.bad_request,
            error=f"Error querying user results",
        )


def construct_response(status_code, body=None, error=None):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps({"body": body, "error": error}),
    }


def get_all_metadata(user_id):
    try:
        table = dynamodb.Table(table_name)
        # fmt: off
        metadata = table.query(KeyConditionExpression=Key('uuid').eq(user_id))['Items']
        # fmt: on
        logger.debug(f"Metadata file: {metadata}")
        return metadata
    except Exception as e:
        logger.error(f"Error getting graph object: {traceback.format_exc()}")
        raise e
