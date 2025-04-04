from openai import OpenAI
import json

# Get the API key (Insert your API key here)
api_key = st.secrets["OPENAI_API_KEY"]

# Initialize OpenAI client with the API key
client = OpenAI(api_key=api_key)

# Read internal prompt from file
with open('system_prompt.txt','r') as file:
	int_prompt = file.read()

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
