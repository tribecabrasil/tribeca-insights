

#!/usr/bin/env bash
set -euo pipefail

# install_certs.sh
# macOS: Install missing SSL certificates for the Python environment

CERT_SCRIPT="$(python - <<'PYCODE'
import sysconfig, os
data_path = sysconfig.get_path('data')
# On macOS, the script is located two levels up in Resources
cert_path = os.path.abspath(os.path.join(data_path, '..', '..', 'Resources', 'Install Certificates.command'))
print(cert_path)
PYCODE
)"

if [ -f "$CERT_SCRIPT" ]; then
    echo "Running Python Install Certificates.command at: $CERT_SCRIPT"
    open "$CERT_SCRIPT"
else
    echo "Certificate installation script not found at expected path: $CERT_SCRIPT"
    exit 1
fi