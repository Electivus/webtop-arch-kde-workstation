"""A local refusing proxy records actual makepkg dependency download attempts."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path

ROOT = Path('/tmp/package-proxy')
ROOT.mkdir(exist_ok=True)
(ROOT / 'connections.jsonl').write_text('')


class Proxy(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def refuse(self):
        with (ROOT / 'connections.jsonl').open('a') as log:
            log.write(json.dumps({'method': self.command, 'target': self.path}) + '\n')
        self.send_error(502, 'Intentional package dependency proxy refusal')

    do_CONNECT = refuse
    do_GET = refuse


server = ThreadingHTTPServer(('127.0.0.1', 31281), Proxy)
(ROOT / 'ready').touch()
server.serve_forever()
