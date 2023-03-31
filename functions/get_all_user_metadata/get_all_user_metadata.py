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
    except Exception as e:
        return construct_response(
            codes.bad_request, "Unable to get UUID from request", str(e)
        )

    try:
        results = get_all_user_metadata(uuid)
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


def get_all_user_metadata(user_id):
    result = []
    bucket = s3.Bucket(user_results_s3_bucket)
    logger.debug(f"Getting user metadata objects from bucket {user_results_s3_bucket}")
    for obj in bucket.objects.filter(Prefix=user_id):
        logger.debug(f"Object key: {obj.key}")
        if obj.key.endswith("metadata.json"):
            logger.debug(f"Getting metadata object: {obj.key}")
            metadata_object = s3.Object(user_results_s3_bucket, obj.key)
            metadata = json.loads(metadata_object.get()["Body"].read())
            result.append(metadata)
    return result
