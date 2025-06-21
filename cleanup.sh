#!/bin/bash
set -euo pipefail

# Delete generated crawl artifacts
rm -f visited_urls_*.csv
rm -rf */pages_md */pages_json *.com/

printf "Artifacts cleaned.\n"
