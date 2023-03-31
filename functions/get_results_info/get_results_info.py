import json
import boto3
import logging
from requests import codes

s3 = boto3.resource("s3")

user_results_s3_bucket = "complexity-analyzer-results-test"

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
            codes.bad_request, error=f"Error querying user results: {str(e)}"
        )


def construct_response(status_code, body=None, error=None):
    body = None
    if error:
        body = {"error": error}
    else:
        body = {"user-metadata": body}

    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": body,
    }


def get_metadata_by_timestamp(user_id, timestamp):
    metadata_object = f"{user_id}/{timestamp}/metadata.json"

    try:
        metadata = (
            s3.Object(user_results_s3_bucket, metadata_object)
            .get()["Body"]
            .read()
            .decode("utf-8")
        )
        logger.debug(f"Metadata file: {metadata}")
        return metadata
    except Exception as e:
        logger.error(f"Error getting graph object: {str(e)}")
        raise e
