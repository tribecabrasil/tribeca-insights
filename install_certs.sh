#!/usr/bin/env bash
set -euo pipefail

log() {
    printf "[%s] %s\n" "$(date '+%Y-%m-%d %H:%M:%S')" "$1"
}

# install_certs.sh
# macOS: Install missing SSL certificates for the Python environment using certifi

INSTALLED_VERSION=$(python3 - <<'PYCODE'
import pkg_resources, sys
try:
    dist = pkg_resources.get_distribution('certifi')
    print(dist.version)
except pkg_resources.DistributionNotFound:
    sys.exit(1)
PYCODE
)
if [ -n "$INSTALLED_VERSION" ]; then
    log "certifi is already installed (version $INSTALLED_VERSION)"
else
    log "certifi not found; installing..."
    python3 -m pip install --upgrade certifi
    if [ $? -ne 0 ]; then
        log "ERROR: certifi installation failed"
        exit 1
    fi
fi

CERTIFI_PATH="$(python3 - <<'PYCODE'
import certifi
print(certifi.where())
PYCODE
)"
log "Using certifi CA bundle at: $CERTIFI_PATH"

log "Testing HTTPS connection to https://www.google.com..."
python3 - <<'PYCODE'
import ssl, urllib.request, sys
try:
    urllib.request.urlopen('https://www.google.com', timeout=5).read()
    print('SSL test passed')
except Exception as e:
    print(f'SSL test failed: {e}')
    sys.exit(1)
PYCODE
log "SSL smoke-test completed"

exit 0