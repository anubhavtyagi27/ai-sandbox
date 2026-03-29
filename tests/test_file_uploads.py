import os
import io
import pytest
from flask import Flask, session
from app.routes import bp
from config import Config

class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'test_uploads')
    SECRET_KEY = 'test-key'

@pytest.fixture
def app():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    app = Flask(__name__, 
                template_folder=os.path.join(base_dir, 'app', 'templates'),
                static_folder=os.path.join(base_dir, 'app', 'static'))
    app.config.from_object(TestConfig)
    app.register_blueprint(bp)
    
    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    yield app
    
    # Cleanup upload folder
    import shutil
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        shutil.rmtree(app.config['UPLOAD_FOLDER'])

@pytest.fixture
def client(app):
    return app.test_client()

def test_instruction_upload_and_persistence(client, app):
    # 1. Upload a file
    data = {
        'system_instruction_upload': (io.BytesIO(b'Test instructions'), 'test.md'),
        'input_mode': 'text',
        'input': 'test prompt',
        'model': 'gpt-4o',
        'provider': 'openai'
    }
    
    with client:
        resp = client.post('/', data=data, content_type='multipart/form-data')
        # If it didn't save, maybe it didn't validate.
        # We can't easily see form errors here without some tricks, 
        # but let's check if the file exists first.
    
    instr_path = os.path.join(app.config['UPLOAD_FOLDER'], 'active_instructions.md')
    if not os.path.exists(instr_path):
        print(f"DEBUG: File not found at {instr_path}")
        print(resp.data.decode())
    assert os.path.exists(instr_path)
    with open(instr_path, 'r') as f:
        assert f.read() == 'Test instructions'

def test_image_upload_and_persistence(client, app):
    # 1. Upload an image
    data = {
        'image_upload': (io.BytesIO(b'fake image data'), 'test.png'),
        'input_mode': 'image',
        'input': 'what is this',
        'model': 'gpt-4o',
        'provider': 'openai'
    }
    
    with client:
        client.post('/', data=data, content_type='multipart/form-data')
    
    # The extension should be preserved in the name
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'active_image.png')
    assert os.path.exists(image_path)

def test_preview_endpoints(client, app):
    # Setup files
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    with open(os.path.join(app.config['UPLOAD_FOLDER'], 'active_instructions.md'), 'w') as f:
        f.write('Active instructions content')
    
    with open(os.path.join(app.config['UPLOAD_FOLDER'], 'active_image.jpg'), 'wb') as f:
        f.write(b'fake jpeg')
        
    # Test instruction preview
    resp = client.get('/api/uploads/instructions')
    assert resp.status_code == 200
    assert resp.json['exists'] is True
    assert resp.json['content'] == 'Active instructions content'
    
    # Test image preview
    resp = client.get('/api/uploads/image')
    assert resp.status_code == 200
    assert resp.data == b'fake jpeg'
