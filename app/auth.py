import os
from functools import wraps
from flask import request, Response


def check_auth(username, password):
    expected_user = os.environ.get('ADMIN_USERNAME', 'admin')
    expected_pass = os.environ.get('ADMIN_PASSWORD', 'changeme')
    return username == expected_user and password == expected_pass


def authenticate():
    return Response(
        'Could not verify your access level.\n'
        'Please log in.', 401,
        {'WWW-Authenticate': 'Basic realm="VCF Depot Manager"'}
    )


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated