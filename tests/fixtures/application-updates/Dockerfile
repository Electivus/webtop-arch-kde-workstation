ARG BASE_IMAGE=electivus/webtop-arch-kde-salesforce:stable
FROM ${BASE_IMAGE}
RUN python3 - <<'PY'
import json
from pathlib import Path
path = Path('/etc/electivus/applications.d/20-salesforce.json')
config = json.loads(path.read_text())
config['salesforce']['cliVersion'] = '2.149.1'
config['salesforce']['cliIntegrity'] = 'sha512-NRys7Wwn7MAbAUzA8kymlbVzOsWlGRO1Jl1dUQ9k0MijqZ5DDYPOh1LNHxQIY34g+Yy0SXNmVe01AVinG4Rcmg=='
path.write_text(json.dumps(config, indent=2))
PY
LABEL org.opencontainers.image.version="application-update-fixture"
