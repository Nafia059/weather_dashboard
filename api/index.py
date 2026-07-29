from http.server import BaseHTTPRequestHandler
import io
import json
import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'weather_dashboard.settings')

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._handle_request('GET')

    def do_POST(self):
        self._handle_request('POST')

    def do_PUT(self):
        self._handle_request('PUT')

    def do_DELETE(self):
        self._handle_request('DELETE')

    def do_PATCH(self):
        self._handle_request('PATCH')

    def _handle_request(self, method):
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length else b''

        environ = {
            'REQUEST_METHOD': method,
            'SERVER_NAME': self.headers.get('Host', 'localhost'),
            'SERVER_PORT': '443',
            'PATH_INFO': self.path,
            'QUERY_STRING': self.path.split('?', 1)[1] if '?' in self.path else '',
            'SERVER_PROTOCOL': self.request_version,
            'wsgi.input': io.BytesIO(body),
            'wsgi.errors': sys.stderr,
            'wsgi.url_scheme': 'https',
        }

        for key, value in self.headers.items():
            key_upper = key.upper().replace('-', '_')
            environ[f'HTTP_{key_upper}'] = value

        response_started = []
        response_body = []

        def start_response(status, headers, exc_info=None):
            response_started.append((status, headers))

        try:
            response = application(environ, start_response)
            status, resp_headers = response_started[0]

            self.send_response(int(status.split(' ')[0]))
            for key, value in resp_headers:
                self.send_header(key, value)
            self.end_headers()

            for chunk in response:
                self.wfile.write(chunk)
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(str(e).encode())
