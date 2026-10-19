#!/usr/bin/env bash
# Upload the site to the VPS.  Usage: ./deploy/deploy.sh user@your-server
set -euo pipefail
SERVER="${1:?usage: ./deploy/deploy.sh user@your-server}"
TARGET="/var/www/stonepark/web/"
ssh "$SERVER" "mkdir -p $TARGET"
rsync -avz --delete --exclude '.DS_Store' web/ "$SERVER:$TARGET"
echo "Done. Open your domain and press Ctrl+F5."
