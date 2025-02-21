# Create a secure credentials directory
import base64
import os
import stat

creds_dir = '/code/astrobin/settings/credentials'
if not os.path.exists(creds_dir):
    os.makedirs(creds_dir, mode=0o700)  # Only readable by owner

if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
    creds_path = os.path.join(creds_dir, 'google-credentials.json')
    creds_content = base64.b64decode(os.environ['GOOGLE_APPLICATION_CREDENTIALS'])

    # Write file with restricted permissions
    with open(creds_path, 'wb') as f:
        os.chmod(creds_path, stat.S_IRUSR | stat.S_IWUSR)  # 0o600 - only owner can read/write
        f.write(creds_content)

    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
