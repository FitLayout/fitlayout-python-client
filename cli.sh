#! /bin/bash
if [ $# -ne 2 ]; then
    echo "Usage: cli.sh <server_url> <repository_id>"
    exit 1
fi

SERVER_URL="$1"
REPOSITORY_ID="$2"

python -i flclient/cli.py "$SERVER_URL" "$REPOSITORY_ID"
