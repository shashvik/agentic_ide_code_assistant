from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from llm_coding_agent.agent import root_agent, list_directory_contents_recursive, read_file_content
import requests
import json
import random
import os

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

class FileChangeHandler(FileSystemEventHandler):
    def on_any_event(self, event):
        socketio.emit('file_change', {'message': 'File system changed'})

BASE_URL = 'http://localhost:8000'  # Update this with your actual base URL

@app.route('/list_apps', methods=['GET'])
def api_list_apps():
    try:
        response = requests.get(f'{BASE_URL}/list-apps', headers={'accept': 'application/json'})
        response.raise_for_status()
        return jsonify(response.json()), 200
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

@app.route('/create_session', methods=['POST'])
def api_create_session():
    data = request.get_json()
    app_name = data.get('app_name')
    user_id = data.get('user_id') or str(random.randint(1000, 9999))
    session_id = data.get('session_id') or str(random.randint(100, 999))

    url = f'{BASE_URL}/apps/{app_name}/users/{user_id}/sessions/{session_id}'
    print(url)
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, headers=headers, data='{}')
        response.raise_for_status()
        return jsonify({'message': 'Session created', 'user_id': user_id, 'session_id': session_id}), 200
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

@app.route('/run_sse', methods=['POST'])
def api_run_sse():
    data = request.get_json()
    app_name = data.get('app_name')
    user_id = data.get('user_id')
    session_id = data.get('session_id')
    prompt = data.get('prompt')

    if not all([app_name, user_id, session_id, prompt]):
        return jsonify({'error': 'Missing required parameters'}), 400

    # Model Armor check
    sanitized_prompt = prompt
    if sanitized_prompt is None:
        return jsonify({'error': 'Prompt denied by Model Armor'}), 403

    # Send to actual SSE endpoint
    url = f'{BASE_URL}/run_sse'
    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }

    payload = {
        "app_name": app_name,
        "user_id": user_id,
        "session_id": session_id,
        "new_message": {
            "parts": [{"text": sanitized_prompt}],
            "role": "user"
        },
        "streaming": True
    }

    full_response_content = ""
    try:
        with requests.post(url, headers=headers, data=json.dumps(payload), stream=True) as response:
            response.raise_for_status()
            print(response)
            for line in response.iter_lines():
                print(line)
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith('data: '):
                        json_str = decoded_line[len('data: '):]
                        try:
                            event_data = json.loads(json_str)
                            if 'content' in event_data and 'parts' in event_data['content']:
                                for part in event_data['content']['parts']:
                                    if 'text' in part:
                                        full_response_content += part['text']
                            if 'partial' in event_data and not event_data['partial']:
                                break
                        except json.JSONDecodeError:
                            continue
        print(f"Raw LLM Response: {full_response_content}")  # Added for debugging
        return jsonify({'response': full_response_content}), 200

    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message')

    if not user_message:
        return jsonify({'error': 'Message is required'}), 400

    try:
        # Create session identifiers
        app_name = "llm_coding_agent"
        user_id = str(random.randint(1000, 9999))
        session_id = str(random.randint(100, 999))

        # Step 1: Create session
        session_url = f'{BASE_URL}/apps/{app_name}/users/{user_id}/sessions/{session_id}'
        session_response = requests.post(
            session_url,
            headers={'accept': 'application/json', 'Content-Type': 'application/json'},
            data='{}'
        )
        session_response.raise_for_status()

        # Step 2: Stream response from SSE endpoint
        sse_url = f'{BASE_URL}/run_sse'
        payload = {
            "app_name": app_name,
            "user_id": user_id,
            "session_id": session_id,
            "new_message": {
                "parts": [{"text": user_message}],
                "role": "user"
            },
            "streaming": True
        }

        full_response_content = ""
        sse_response = requests.post(
            sse_url,
            headers={'accept': 'application/json', 'Content-Type': 'application/json'},
            json=payload,
            stream=True,
            timeout=30
        )

        for line in sse_response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith('data: '):
                    json_str = decoded_line[len('data: '):]
                    try:
                        event_data = json.loads(json_str)
                        if 'content' in event_data and 'parts' in event_data['content']:
                            for part in event_data['content']['parts']:
                                if 'text' in part:
                                    full_response_content += part['text']
                        if 'partial' in event_data and not event_data['partial']:
                            break
                    except json.JSONDecodeError:
                        continue

        print(f"Raw LLM Response: {full_response_content}")

        # Step 3: Detect language based on user message
        language = 'python'  # Default
        message_lower = user_message.lower()
        if 'javascript' in message_lower or 'react' in message_lower:
            language = 'javascript'
        elif 'python' in message_lower:
            language = 'python'

        return jsonify({
            'response': "Here's what I generated for you:",
            'code': full_response_content,
            'language': language
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

import subprocess

@app.route('/api/run', methods=['POST'])
def run_code():
    data = request.json
    code = data.get('code')
    language = data.get('language')

    if not code or not language:
        return jsonify({'error': 'Code or language not provided'}), 400

    try:
        if language == 'python':
            file_ext = 'py'
            cmd = ['python3']
        elif language == 'javascript':
            file_ext = 'js'
            cmd = ['node']
        else:
            return jsonify({'error': 'Unsupported language'}), 400

        # Create a temporary file to write the code
        with open(f'temp.{file_ext}', 'w') as f:
            f.write(code)

        # Execute the code in a subprocess
        result = subprocess.run(
            cmd + [f'temp.{file_ext}'],
            capture_output=True,
            text=True,
            timeout=10  # 10-second timeout for security
        )

        # Clean up the temporary file
        os.remove(f'temp.{file_ext}')

        output = result.stdout
        if result.stderr:
            output += result.stderr

        return jsonify({'output': output})

    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Code execution timed out (10 seconds limit).'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files', methods=['GET'])
def list_files():
    try:
        files = list_directory_contents_recursive('.')
        return jsonify(files)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/files/<path:file_path>', methods=['GET'])
def get_file_content(file_path):
    try:
        content = read_file_content(file_path)
        return jsonify({'content': content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    path = os.path.abspath("agentic_coder")
    if not os.path.exists(path):
        os.makedirs(path)
    event_handler = FileChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    socketio.run(app, debug=True, port=5000)