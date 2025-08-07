import json

def handler(event, context):
    """A simple test function."""
    return {
        'statusCode': 200,
        'headers': { 'Content-Type': 'application/json' },
        'body': json.dumps({ 'message': 'The API is online and working!' })
    }
