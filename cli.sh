#! /bin/bash
if [ $# -ne 1 ]; then
    echo "Usage: cli.sh <server_url>"
    exit 1
fi

SERVER_URL="$1"

python -i flclient/cli.py "$SERVER_URL"
