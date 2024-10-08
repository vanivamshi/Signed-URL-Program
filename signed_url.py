pip install flask

from flask import Flask, request, abort
import hmac
import hashlib
import time
import logging
import os

app = Flask(__name__)

# Load configuration from environment variables or a secure key management system
KEY_VERSIONS = {
    'v1': os.getenv('SECRET_KEY_V1', 'defaultsecretkeyv1'),
    'v2': os.getenv('SECRET_KEY_V2', 'defaultsecretkeyv2')
}

ALLOWED_IPS = set(os.getenv('ALLOWED_IPS', '127.0.0.1').split(','))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_signed_url(base_url, secret_key, expiration_time, key_version):
    """
    Generate a signed URL with expiration time and key version.
    """
    to_sign = f"{base_url}?expires={expiration_time}&version={key_version}"
    signature = hmac.new(secret_key.encode(), to_sign.encode(), hashlib.sha256).hexdigest()
    signed_url = f"{base_url}?expires={expiration_time}&version={key_version}&signature={signature}"
    return signed_url

def verify_signature(url, signature, secret_key):
    """
    Verify the signature of the URL.
    """
    to_sign = url.split('&signature=')[0]
    calculated_signature = hmac.new(secret_key.encode(), to_sign.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(calculated_signature, signature)

@app.route('/resource')
def resource():
    expires = request.args.get('expires')
    signature = request.args.get('signature')
    version = request.args.get('version')

    if request.remote_addr not in ALLOWED_IPS:
        logger.warning('IP address not allowed')
        abort(403, 'IP address not allowed')

    if not expires or not signature or not version:
        logger.error('Missing parameters')
        abort(400, 'Missing parameters')

    if version not in KEY_VERSIONS:
        logger.error('Invalid key version')
        abort(400, 'Invalid key version')

    try:
        expiration_time = int(expires)
    except ValueError:
        logger.error('Invalid expiration time')
        abort(400, 'Invalid expiration time')

    if time.time() > expiration_time:
        logger.info('URL has expired')
        abort(403, 'URL has expired')

    secret_key = KEY_VERSIONS[version]
    url = request.url.split('&signature=')[0]
    if not verify_signature(url, signature, secret_key):
        logger.warning('Invalid signature')
        abort(403, 'Invalid signature')

    logger.info('Access granted')
    return 'Access granted'

if __name__ == '__main__':
    # Generate a signed URL (for demonstration purposes)
    base_url = "http://localhost:5000/resource"
    expiration_time = int(time.time()) + 3600  # 1 hour from now
    key_version = 'v2'  # Use the current key version
    signed_url = generate_signed_url(base_url, KEY_VERSIONS[key_version], expiration_time, key_version)
    print("Generated Signed URL:", signed_url)

    # Run the Flask server
    app.run(debug=True)
