import json
import logging
from requests import codes
import boto3
import csv

# This function gets the graph to display on the frontend, not to download

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
            codes.bad_request, f"Invalid user ID header: {str(e)}"
        )

    try:
        results = get_result_graph_as_json(uuid, timestamp)
        if not results or len(results) == 0:
            return construct_response(
                codes.not_found, f"No results found for user {uuid}"
            )
        else:
            return construct_response(codes.ok, body=results)
    except Exception as e:
        return construct_response(
            codes.internal_server_error, error=f"Error querying user results: {str(e)}"
        )


def get_result_graph_as_json(user_id, timestamp):
    graph_object = f"{user_id}/{timestamp}/graph.csv"

    result = []

    try:
        csv_graph = s3.Object(user_results_s3_bucket, graph_object)
        csv_file = csv_graph.get()["Body"].read().decode("utf-8")
        logger.debug(f"CSV file: {csv_file}")
        rows = csv_file.split("\n")
        for row in rows:
            try:
                x, y = row.split(",")
                y.replace("\r", "")
            except Exception as e:
                logger.error(f"Error parsing row: {str(e)}")
                continue
            result.append({"x": x, "y": y})
        return result
    except Exception as e:
        logger.error(f"Error getting graph object: {str(e)}")
        raise e


def construct_response(status_code, body=None, error=None):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps({"body": body, "error": error}),
    }
