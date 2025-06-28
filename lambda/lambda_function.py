import json
import os
import boto3

# Initialize the DynamoDB client
# The region is automatically picked up from the Lambda environment
dynamodb = boto3.resource('dynamodb')

# Get the DynamoDB table name from environment variables
# This will be set by CloudFormation
TABLE_NAME = os.environ.get('DYNAMODB_TABLE_NAME')
if not TABLE_NAME:
    print("Error: DYNAMODB_TABLE_NAME environment variable not set.")
    # In a production scenario, you might raise an exception or handle this more gracefully.
    # For this example, we'll proceed, but operations will fail if the table name is missing.

# The primary key for the item in DynamoDB where we store the last name
# We'll use a fixed key since we only need to store one "setting"
NAME_SETTING_KEY = "last_user_name"

def handler(event, context):
    """
    AWS Lambda function handler for the web application.
    It handles GET requests to retrieve the current greeting and POST requests
    to update the user's name and generate a new greeting.
    """
    print(f"Received event: {json.dumps(event)}")

    # Set up CORS headers to allow requests from any origin
    # In a production environment, you should restrict 'Access-Control-Allow-Origin'
    # to your specific website domain (e.g., 'https://yourwebsite.com').
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*', # Allow all origins for simplicity in this example
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
    }

    try:
        table = dynamodb.Table(TABLE_NAME)
    except Exception as e:
        print(f"Error accessing DynamoDB table: {e}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'message': 'Internal Server Error: Could not access database.'})
        }

    # Handle pre-flight OPTIONS request from browsers (CORS)
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }

    # Handle GET request: Retrieve and display the last entered name or a default greeting
    if event.get('httpMethod') == 'GET':
        try:
            response = table.get_item(Key={'SettingName': NAME_SETTING_KEY})
            last_name = response.get('Item', {}).get('Value') # Get the 'Value' attribute from the item

            if last_name:
                message = f"Greetings, {last_name} Welcome to Tech World."
            else:
                message = "Hello, Welcome to Tech World."

            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'message': message})
            }
        except Exception as e:
            print(f"Error getting item from DynamoDB: {e}")
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps({'message': 'Error retrieving greeting.'})
            }

    # Handle POST request: Receive a new name, store it, and generate a new greeting
    elif event.get('httpMethod') == 'POST':
        try:
            # Parse the request body to get the name
            body = json.loads(event.get('body', '{}'))
            user_name = body.get('name', '').strip()

            if not user_name:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'message': 'Name is required in the request body.'})
                }

            # Store the new name in DynamoDB
            table.put_item(
                Item={
                    'SettingName': NAME_SETTING_KEY, # Fixed key for this setting
                    'Value': user_name # The actual name value
                }
            )

            message = f"Greetings, {user_name} Welcome to Tech World."

            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'message': message})
            }
        except json.JSONDecodeError:
            print("Error: Invalid JSON in request body.")
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'message': 'Invalid JSON in request body.'})
            }
        except Exception as e:
            print(f"Error putting item to DynamoDB: {e}")
            return {
                'statusCode': 500,
                'headers': headers,
                'body': json.dumps({'message': 'Error updating greeting.'})
            }
    else:
        # For any other HTTP methods
        return {
            'statusCode': 405, # Method Not Allowed
            'headers': headers,
            'body': json.dumps({'message': 'Method Not Allowed'})
        }
