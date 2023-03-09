import json
import boto3
from requests import codes

dynamodb = boto3.client('dynamodb')

s3client = boto3.client('s3')

dynamodb_user_id_table = 'complexity-analyzer-users'

user_results_s3_bucket = 'complexity-analyzer-results-test'

def lambda_handler(event, context):

    try:
        user_id = event['user-id']
    except Exception as e:
        return construct_response(codes.bad_request, 'Invalid user ID header', str(e))

    if is_valid_user_id(user_id):
        # Query for User's Results
        results = query_user_results(user_id)
        # TODO: Modify response to contain results with user results metadata
        return construct_response(codes.ok, 'User ID header validated successfully')
    else:
        return construct_response(codes.bad_request, 'Invalid user ID')


def construct_response(status_code, message, error=None):
    if error:
        response = {
            'statusCode': status_code,
            'body': json.dumps({'message': message, 'error': error})
        }
    else:
        response = {
            'statusCode': status_code,
            'body': json.dumps({'message': message})
        }
    return response


#TODO: Abstract this into a separate lambda function
def is_valid_user_id(uuid):
    params = {
        'TableName': dynamodb_user_id_table,
        'KeyConditionExpression': 'uuid = :uuid',
        'ExpressionAttributeValues': {
            ':uuid': {'S': uuid}
        }
    }

    response = dynamodb.query(**params)

    return response['Count'] == 1

def query_user_results(user_id):
    # Define the parameters for the query
    params = {
        'Bucket': user_results_s3_bucket,
        'Prefix': user_id
    }

    # Query the S3 bucket
    response = s3client.list_objects_v2(**params)

    return response