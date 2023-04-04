from io import StringIO
import json
import boto3
from requests import codes
import logging
import time
import csv
import traceback

s3 = boto3.resource("s3")
bucket_name = "complexity-analyzer-results-test"

dynamodb = boto3.resource("dynamodb")
table_name = "complexity-analyzer-metadata-db"

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def lambda_handler(event, context):
    try:
        inputCode = event["inputCode"]
        args = event["args"]
        complexity = event["complexity"]
        user_id = event["user-id"]
        complexity_graph = event["complexity-graph"]
        description = event["description"]
        logger.debug(
            f"Input code: {inputCode}, args: {args}, complexity: {complexity}, user-id: {user_id}, complexity-graph: {complexity_graph}"
        )
        post_metadata_to_dynamo_db(inputCode, args, complexity, user_id, description)
        post_complexity_graph_to_s3(user_id, complexity_graph)
    except Exception as e:
        return {
            "statusCode": codes.internal_server_error,
            "body": json.dumps({"error": str(e)}),
        }


def post_metadata_to_dynamo_db(inputCode, args, complexity, user_id, description):
    try:
        timestamp = str(int(time.time()))
        table = dynamodb.Table(table_name)
        table.put_item(
            Item={
                "uuid": user_id,
                "timestamp": timestamp,
                "inputCode": inputCode,
                "args": args,
                "complexity": complexity,
                "description": description,
            }
        )
    except Exception as e:
        logger.error(f"Failed to write to dynamodb: {traceback.format_exc()}")
        raise e


def post_complexity_graph_to_s3(user_id, complexity_graph):
    # Timestamps are unique, so we can use them as keys
    timestamp = str(int(time.time()))
    prefix = f"{user_id}/{timestamp}"
    logger.debug(f"Prefix: {prefix}")

    bucket = s3.Bucket(bucket_name)
    prefix_in_bucket = list(bucket.objects.filter(Prefix=prefix))
    if len(prefix_in_bucket) > 0:
        logger.error(f"Prefix {prefix} already exists in bucket {bucket_name}")
        raise Exception(f"Prefix {prefix} already exists in bucket {bucket_name}")

    try:
        complexity_graph_object_key = f"{prefix}/graph.csv"
        logger.debug(f"complexity_graph_object_key: {complexity_graph_object_key}")

        s3_graph_object = s3.Object(bucket_name, complexity_graph_object_key)
        logger.debug(f"Writing to s3 object: {s3_graph_object}")

        graph_bytes = parseToCsv(complexity_graph)
        logger.debug(f"graph_bytes: {graph_bytes}")

        s3_graph_object.put(Body=graph_bytes)
        logger.debug("Successfully wrote to s3 graph.csv object")
    except Exception as e:
        logger.error(f"Failed to write to s3 graph.csv object: {e}")
        raise e


def parseToCsv(complexity_graph):
    csv_data = StringIO()
    csv_writer = csv.writer(csv_data)
    csv_writer.writerows(complexity_graph)
    return csv_data.getvalue().encode("utf-8")
