import base64
import os
import stat

creds_dir = '/code/astrobin/settings/credentials'
if not os.path.exists(creds_dir):
    os.makedirs(creds_dir, mode=0o700)  # Only readable by owner

if 'GOOGLE_APPLICATION_CREDENTIALS_BASE64' in os.environ:
    creds_path = os.path.join(creds_dir, 'google-credentials.json')
    creds_content = base64.b64decode(os.environ['GOOGLE_APPLICATION_CREDENTIALS_BASE64'])

    # Write file with restricted permissions
    flags = os.O_WRONLY | os.O_CREAT
    mode = stat.S_IRUSR | stat.S_IWUSR  # 0o600

    fd = os.open(creds_path, flags, mode)
    with os.fdopen(fd, 'wb') as f:
        f.write(creds_content)

    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = creds_path
