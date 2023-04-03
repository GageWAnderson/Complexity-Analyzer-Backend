import json
import boto3
import logging
from requests import codes
import traceback

s3 = boto3.client("s3")

user_results_s3_bucket = "complexity-analyzer-results-test"

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
        res = []
        response = s3.list_objects_v2(Bucket=user_results_s3_bucket, Prefix=user_id)
        for object in response["Contents"]:
            if object["Key"].endswith("metadata.json"):
                # fmt: off
                metadata = s3.get_object(Bucket=user_results_s3_bucket, Key=object['Key'])['Body'].read().decode('utf-8')
                # fmt: on
                res.append({"metadata": metadata})
        return res
    except Exception as e:
        logger.error(f"Error getting graph object: {traceback.format_exc()}")
        raise e
