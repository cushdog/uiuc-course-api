#!/bin/bash

# Load environment variables from .env.local
if [ -f .env.local ]; then
  export $(cat .env.local | xargs)
fi

bump deploy \
  --doc "classify-api" \
  --token "$BUMP_TOKEN" \
  api-documentation.yml