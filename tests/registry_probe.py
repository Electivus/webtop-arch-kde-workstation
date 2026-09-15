"""Read the owned engine-loopback registry independently of Docker image metadata."""
import hashlib
import json
import sys
import urllib.request

request = urllib.request.Request(sys.argv[1], headers={'Accept': ', '.join([
    'application/vnd.oci.image.index.v1+json',
    'application/vnd.docker.distribution.manifest.list.v2+json',
    'application/vnd.oci.image.manifest.v1+json',
    'application/vnd.docker.distribution.manifest.v2+json',
])})
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
with opener.open(request, timeout=10) as response:
    content = response.read()
    print(json.dumps({'status': response.status,
        'headers': {key.lower(): value for key, value in response.headers.items()},
        'sha256': 'sha256:' + hashlib.sha256(content).hexdigest(),
        'body': json.loads(content)}))
