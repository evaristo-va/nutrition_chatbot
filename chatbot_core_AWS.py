import boto3
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv
from openai import OpenAI
import json

# Function to get the secrets AWS Secrets Manager
def get_secret():

    secret_name = "OPENAI_API_KEY"  # Name of your secret in AWS Secrets Manager (API Key)
    region_name = "us-east-2"  # AWS region

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        # Fetch secret value
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        raise e

    # Parse the secret string (stored as JSON)
    secret = get_secret_value_response['SecretString']
    secret_dict = json.loads(secret)

    # Extract the API key dictionary
    api_key = secret_dict.get('OPENAI_API_KEY', None)

    if api_key is None:
        raise ValueError("API key not found in the secret")

    return api_key


# Function to get system prompt from S3 storage
def load_prompt_from_s3(bucket_name='streamlit-chatbot-database', file_key='system_prompt.txt'):
    s3 = boto3.client('s3')
    response = s3.get_object(Bucket=bucket_name, Key=file_key)
    content = response['Body'].read().decode('utf-8')
    return content

# Get the OpenAI API key from Secrets Manager
api_key = get_secret()

# Read internal prompt from file S3
int_prompt = load_prompt_from_s3()

# Initialize OpenAI client with the API key
client = OpenAI(api_key=api_key)

# Function defined 
def check_tdee(gender, age, weight, height, goal, activity_level):
	if gender == 'male':
		BMR = 10 * weight + 6.25 * height - 5 * age + 5
	elif gender == 'female':
		BMR = 10 * weight + 6.25 * height - 5 * age - 161

	TDEE = BMR * activity_level
	
	# Lose fat
	if goal == 1:
		TDEE = TDEE-250
	# Gain muscle
	elif goal == 2:
		TDEE = TDEE+250

	return TDEE

# Function to interact with OpenAI GPT-4 model using the completions endpoint
def get_gpt_response(conversation, tools):
    completion = client.chat.completions.create(
        model="gpt-4o", 
	messages=conversation,
	tools=tools 
    )
    
    # Extract and return the response text
    gpt_response = completion.choices[0].message.content
    gpt_tool = completion.choices[0].message.tool_calls

    return gpt_response, gpt_tool

# This is to call the function (for now I have implemented only one function but more can be implemented)
def call_function(name,args):
	if name == "check_tdee":
		return(check_tdee(**args))

def get_tools():
	# Define the tools to be used
	return [{
	    "type": "function",
	    "function": {
	        "name": "check_tdee",
	        "description": "Calculate the user's total energy expenditure.",
	        "parameters": {
	            "type": "object",
	            "properties": {
			"gender": {
				"type": "string",
				"enum": ["male", "female"],
				"description" : "The user's gender (male or female)"
			},
			"age": {
				"type": "integer",
				"description": "User's age in years."
			},
			"weight": {
				"type": "number",
				"description": "User's weight in kg."
			},
			"height": {
				"type": "number",
				"description": "User's height in cm."
			},
			"goal": {
				"type": "integer",
				"enum": [0,1,2],
				"description": "0 = Maintain weight, 1 = Lose fat, 2 = Gain muscle."
			},
			"activity_level": {
				"type": "number",
				"enum": [1.2,1.375,1.55,1.725,1.9],
				"description" : "Activity level multiplier"
			} 
	            },
	            "required": ["gender", "age", "weight", "height", "goal", "activity_level"]
	        }
	    }
	}]
