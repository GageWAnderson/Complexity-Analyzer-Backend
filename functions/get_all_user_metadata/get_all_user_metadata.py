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
        results = get_all_metadata(uuid)
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
                metadata = (
                    s3.Object(user_results_s3_bucket, object["Key"])
                    .get()["Body"]
                    .read()
                    .decode("utf-8")
                )
                res.append({"timestamp": object["Key"].split("/")[1], "metadata": metadata})
        logger.debug(f"Metadata file: {res}")
        return res
    except Exception as e:
        logger.error(f"Error getting graph object: {str(e)}")
        raise e
