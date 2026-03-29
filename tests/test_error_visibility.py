import os
import io
import pytest
from flask import Flask
from app.routes import bp
from config import Config

class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'test_uploads_errors')
    SECRET_KEY = 'test-key'

@pytest.fixture
def app():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    app = Flask(__name__, 
                template_folder=os.path.join(base_dir, 'app', 'templates'),
                static_folder=os.path.join(base_dir, 'app', 'static'))
    app.config.from_object(TestConfig)
    app.register_blueprint(bp)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    yield app
    import shutil
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        shutil.rmtree(app.config['UPLOAD_FOLDER'])

@pytest.fixture
def client(app):
    return app.test_client()

def test_hidden_error_messages(client, app):
    # 1. Setup an active instructions file so the "Replace" UX is active
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    with open(os.path.join(app.config['UPLOAD_FOLDER'], 'active_instructions.md'), 'w') as f:
        f.write('initial content')
        
    # 2. Upload an invalid file type (e.g., .exe)
    data = {
        'system_instruction_upload': (io.BytesIO(b'malicious'), 'test.exe'),
        'input_mode': 'text',
        'input': 'test prompt',
        'model': 'gpt-4o',
        'provider': 'openai'
    }
    
    resp = client.post('/', data=data, content_type='multipart/form-data')
    html = resp.data.decode()
    
    # Check if error message is present
    assert 'Markdown or text files only' in html
    
    # Check if the error message is inside a d-none div
    # In the current implementation:
    # <div class="d-none" id="replaceInstructionsInput">
    #     ...
    #     <div class="invalid-feedback d-block">Markdown or text files only</div>
    # </div>
    
    import re
    # The replace div must be visible (no d-none) when there are field errors
    match = re.search(r'<div id="replaceInstructionsInput" class="([^"]*)">', html)
    assert match is not None, "replaceInstructionsInput div not found"
    classes = match.group(1).split()
    assert 'd-none' not in classes, "replaceInstructionsInput should be visible when there are errors"
