import os

bind = f"{os.environ.get('FLASK_HOST', '0.0.0.0')}:{os.environ.get('FLASK_PORT', '5000')}"
workers = int(os.environ.get('GUNICORN_WORKERS', '4'))
timeout = int(os.environ.get('GUNICORN_TIMEOUT', '120'))
accesslog = os.environ.get('LOG_DIR', '/data/logs') + '/gunicorn-access.log'
errorlog = os.environ.get('LOG_DIR', '/data/logs') + '/gunicorn-error.log'
loglevel = 'info'
preload_app = True