from flask import Flask, render_template, request, jsonify
import requests
import time

app = Flask(__name__)

# OpenAI API details
API_KEY = 'YOUR_API_KEY'
API_URL = 'https://api.openai.com/v1/chat/completions'

# Function to call the OpenAI API with retry and exponential backoff
def call_openai_api(data, retries=5, delay=1):
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {API_KEY}',
    }

    for attempt in range(retries):
        try:
            response = requests.post(API_URL, headers=headers, json=data)
            response.raise_for_status()  # Raise an error for 4xx/5xx responses
            return response.json()  # Return the API response on success

        except requests.exceptions.HTTPError as http_err:
            # Check if it's a rate limit error
            if response.status_code == 429:
                if attempt < retries - 1:
                    wait_time = delay * (2 ** attempt)  # Exponential backoff
                    print(f"Rate limit hit. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)  # Wait before retrying
                else:
                    return {'error': 'Rate limit exceeded. Please try again later.'}
            else:
                return {'error': f'HTTP error occurred: {http_err}'}
        
        except Exception as err:
            return {'error': f'Other error occurred: {err}'}

    return {'error': 'Failed to connect to the API after retries.'}

# Home route to render the simple HTML form
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle user input and return ChatGPT response
@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.form['message']
    
    # Prepare the data to send to the OpenAI API
    data = {
        "model": "gpt-4",  # or "gpt-3.5-turbo"
        "messages": [{"role": "user", "content": user_input}]
    }
    
    # Call OpenAI API with retry and exponential backoff
    response_data = call_openai_api(data)
    
    # Handle API errors
    if 'error' in response_data:
        return jsonify({'reply': response_data['error']})
    
    # Extract the model's response
    model_reply = response_data['choices'][0]['message']['content']
    
    return jsonify({'reply': model_reply})

if __name__ == '__main__':
    app.run(debug=True)
