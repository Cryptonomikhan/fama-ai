#!/bin/bash

# Simple script for testing API with stream functionality

API_URL="http://localhost:8000"
API_KEY="test_key"

function submit_request() {
  echo "Submitting new request..."
  curl -s -X POST "$API_URL/api/submit" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d '{
      "description": "A small real estate fund that invests in AI server farms.",
      "time_horizon": 3,
      "risk_factors": "moderate",
      "output_format": "json",
      "use_team_approach": false,
      "stream_updates": true
    }' | jq '.'
  
  echo -e "\nCopy the request_id from above to use with ./simple-stream.sh stream <request_id>"
}

function connect_stream() {
  if [ -z "$1" ]; then
    echo "Error: Please provide a request ID"
    echo "Usage: $0 stream <request_id>"
    exit 1
  fi
  
  echo "Connecting to stream for request $1..."
  echo "----------------------------------------"
  curl -N "$API_URL/api/stream/$1" -H "X-API-Key: $API_KEY"
}

# Main script logic
if [ "$1" = "stream" ]; then
  connect_stream "$2"
elif [ "$1" = "submit" ]; then
  submit_request
else
  echo "Usage: $0 submit | stream <request_id>"
  echo ""
  echo "Commands:"
  echo "  submit            Submit a new request"
  echo "  stream <id>       Connect to the stream for an existing request"
fi 