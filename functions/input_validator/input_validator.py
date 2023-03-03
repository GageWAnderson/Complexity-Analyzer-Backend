import json

def lambda_handler(event, context):
    input = event['body']
    return {
        'statusCode': 200,
        'body': json.dumps(input)
    }
