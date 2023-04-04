import json
import boto3
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
        timestamp = event["queryStringParameters"]["timestamp"]
    except Exception as e:
        return construct_response(
            codes.bad_request, "Unable to get UUID from request", str(e)
        )

    try:
        results = get_metadata_by_timestamp(uuid, timestamp)
        if not results:
            return construct_response(
                codes.not_found, f"No results found for user {uuid}"
            )
        else:
            return construct_response(codes.ok, body=results)
    except Exception as e:
        return construct_response(
            codes.bad_request, error=f"Error querying user results: {traceback.format_exc()}"
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


def get_metadata_by_timestamp(user_id, timestamp):
    try:
        table = dynamodb.Table(table_name)
        metadata = table.get_item(
            Key={"partition_key": user_id, "sort_key": timestamp}
        )["Item"]
        logger.debug(f"Metadata file: {metadata}")
        return metadata
    except Exception as e:
        logger.error(f"Error getting graph object: {traceback.format_exc()}")
        raise e
