"""Disposable HTTPS origins and a real CONNECT proxy, with no external credentials."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import select
import socket
import ssl
import subprocess
import threading

ROOT = Path('/tmp/network-fixture')
ROOT.mkdir(exist_ok=True)


def certificate(label):
    ca, key, leaf, leafkey = [ROOT / (label + suffix) for suffix in ('.crt', '.key', '-leaf.crt', '-leaf.key')]
    subprocess.run(['openssl', 'req', '-new', '-x509', '-newkey', 'rsa:2048', '-noenc', '-days', '2',
                    '-subj', '/CN=Workstation test ' + label, '-addext', 'basicConstraints=critical,CA:TRUE',
                    '-addext', 'keyUsage=critical,keyCertSign,cRLSign',
                    '-keyout', str(key), '-out', str(ca)], check=True, capture_output=True)
    csr = ROOT / (label + '.csr')
    subprocess.run(['openssl', 'req', '-new', '-newkey', 'rsa:2048', '-noenc', '-subj', '/CN=network-target',
                    '-keyout', str(leafkey), '-out', str(csr)], check=True, capture_output=True)
    extensions = ROOT / 'extensions'
    extensions.write_text('subjectAltName=DNS:network-target\nbasicConstraints=critical,CA:FALSE\nextendedKeyUsage=serverAuth\n')
    subprocess.run(['openssl', 'x509', '-req', '-in', str(csr), '-CA', str(ca), '-CAkey', str(key),
                    '-CAcreateserial', '-days', '2', '-extfile', str(extensions), '-out', str(leaf)],
                   check=True, capture_output=True)
    return leaf, leafkey


class Origin(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_GET(self):
        if self.path.startswith('/services/'):
            body = json.dumps([{'errorCode': 'INVALID_SESSION_ID', 'message': 'NETWORK_FIXTURE_AUTH_REJECTED'}]).encode()
            self.send_response(401)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        body = b'' if '/info/refs' in self.path else b'workstation-network-ok'
        if self.path == '/HEAD':
            body = b'ref: refs/heads/main\n'
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class Proxy(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_CONNECT(self):
        if os.environ.get('WORKSTATION_TEST_PROXY_REFUSE') == '1':
            self.send_error(407, 'Rejected demo-user / p@ss-test-123 (http://demo-user:p%40ss-test-123@proxy.example:8080)')
            return
        host, port = self.path.rsplit(':', 1)
        with (ROOT / 'connections.jsonl').open('a') as log:
            log.write(json.dumps({'host': host, 'port': int(port)}) + '\n')
        try:
            upstream = socket.create_connection((host, int(port)), timeout=20)
        except OSError:
            self.send_error(502, 'upstream unavailable')
            return
        self.send_response(200, 'Connection established')
        self.end_headers()
        with upstream:
            peers = [self.connection, upstream]
            while readable := select.select(peers, [], [], 30)[0]:
                for source in readable:
                    data = source.recv(65536)
                    if not data:
                        return
                    destination = upstream if source is self.connection else self.connection
                    destination.sendall(data)


for label, port in [('trusted', 4443), ('untrusted', 4444)]:
    cert, key = certificate(label)
    server = ThreadingHTTPServer(('0.0.0.0', port), Origin)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert, key)
    server.socket = context.wrap_socket(server.socket, server_side=True)
    threading.Thread(target=server.serve_forever, daemon=True).start()
(ROOT / 'ready').touch()
ThreadingHTTPServer(('0.0.0.0', 3128), Proxy).serve_forever()
