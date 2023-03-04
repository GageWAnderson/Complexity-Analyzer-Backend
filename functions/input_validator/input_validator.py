import json
import pandas as pd

def lambda_handler(event, context):
    input = event['body']
    df = pd.DataFrame(data=None)
    return {
        'statusCode': 200,
        'body': json.dumps(input)
    }
