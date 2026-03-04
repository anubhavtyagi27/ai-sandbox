import requests
from bs4 import BeautifulSoup

def test_app():
    session = requests.Session()
    base_url = "http://127.0.0.1:5001"

    # 1. Get the page to fetch CSRF token
    print(f"Fetching {base_url}...")
    try:
        response = session.get(base_url)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to app. Is it running?")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    csrf_token = soup.find('input', {'name': 'csrf_token'})['value']
    print(f"Got CSRF token: {csrf_token}")

    # 2. Test Text Mode
    print("\nTesting Text Mode...")
    data_text = {
        'csrf_token': csrf_token,
        'provider': 'openai',
        'model': 'gpt-4o',
        'input_mode': 'text',
        'input': 'Explain the difference between input_text and input_image in one sentence.',
        'max_tokens': 50
    }
    
    resp_text = session.post(base_url, data=data_text)
    
    if "Response received successfully" in resp_text.text or "Response Content" in resp_text.text:
        print("✅ Text Mode Success!")
    else:
        print("❌ Text Mode Failed!")
        # Print error from page if possible
        soup_err = BeautifulSoup(resp_text.text, 'html.parser')
        alerts = soup_err.find_all(class_='alert-danger')
        for alert in alerts:
            print(f"Error Alert: {alert.get_text().strip()}")

    # 3. Test Image Mode
    print("\nTesting Image Mode...")
    # Need to fetch a fresh token or use the same session? 
    # Usually same session is fine, but let's be safe and refetch if needed, 
    # or just reuse if the token hasn't rotated. Flask-WTF tokens are usually per session/time.
    # Let's reuse.
    
    data_image = {
        'csrf_token': csrf_token,
        'provider': 'openai',
        'model': 'gpt-4o',
        'input_mode': 'image',
        'image_path': '/Users/anubhav/Library/Mobile Documents/com~apple~CloudDocs/Downloads/Mac Downloads/kf-easy-chicken-tacos-gwfh-mediumSquareAt3X.jpg',
        'input': 'Describe this image briefly.'
    }

    resp_image = session.post(base_url, data=data_image)

    if "Response received successfully" in resp_image.text or "Response Content" in resp_image.text:
        print("✅ Image Mode Success!")
    else:
        print("❌ Image Mode Failed!")
        soup_err = BeautifulSoup(resp_image.text, 'html.parser')
        alerts = soup_err.find_all(class_='alert-danger')
        for alert in alerts:
            print(f"Error Alert: {alert.get_text().strip()}")

if __name__ == "__main__":
    test_app()
