from flask import Flask, jsonify, request, send_file, Response
from flask_cors import CORS
import boto3
from botocore.exceptions import NoCredentialsError
from datetime import datetime
import io
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Load environment variables
BUCKET_NAME = os.getenv('WEBCAMTIMELAPSE_BUCKET_NAME')
if not BUCKET_NAME:
    raise ValueError("No BUCKET_NAME environment variable set")

s3 = boto3.client('s3')

# Declare cached_files at the top level
cached_files = []

def update_cache():
    global cached_files

    new_files = []

    # Determine the last file in the cache
    if cached_files:
        last_file = cached_files[-1]
    else:
        last_file = None

    while True:
        if last_file:
            response = s3.list_objects_v2(Bucket=BUCKET_NAME, StartAfter=last_file)
        else:
            response = s3.list_objects_v2(Bucket=BUCKET_NAME)

        if 'Contents' in response:
            for item in response['Contents']:
                if item['Key'] not in cached_files:
                    new_files.append(item['Key'])

        if response.get('IsTruncated'):  # Check if there are more pages
            last_file = response['Contents'][-1]['Key']
        else:
            break

    # Update the cache with new files
    cached_files.extend(new_files)
    cached_files = sorted(cached_files)  # Sort the cached files
    
    print(f'Loaded {len(new_files)}/{len(cached_files)} new files into cache')

@app.route('/list-files', methods=['GET'])
def list_files():
    global cached_files
    update_cache()

    return jsonify(cached_files)

@app.route('/get-file', methods=['GET'])
def get_file():
    file_key = request.args.get('file_key')
    print(f'get-file: {file_key}')
    if not file_key:
        return jsonify({'error': 'file_key parameter is required'}), 400

    try:
        file_obj = s3.get_object(Bucket=BUCKET_NAME, Key=file_key)
        file_content = file_obj['Body'].read()
        mime_type = 'image/jpeg'  # Default MIME type
        print(f'MIME type: {mime_type}')
        
        # Create a response object and set the Content-Disposition header to inline
        response = Response(io.BytesIO(file_content), mimetype=mime_type)
        response.headers['Content-Disposition'] = 'inline; filename="{}"'.format(file_key)
        return response
    except s3.exceptions.NoSuchKey:
        return jsonify({'error': 'File not found'}), 404
    except NoCredentialsError:
        return jsonify({'error': 'Credentials not available'}), 403

if __name__ == '__main__':
    update_cache()
    app.run(debug=True, host='0.0.0.0')
