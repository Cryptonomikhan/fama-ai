#!/bin/bash

# Script to test streaming API for Fama AI

# Make a request to get a request ID
echo "Submitting request..."
RESPONSE=$(curl -s -X POST http://localhost:8000/api/submit \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test_key" \
  -d '{
    "description": "A small real estate fund that invests in AI server farms.",
    "time_horizon": 3,
    "risk_factors": "moderate",
    "output_format": "json",
    "use_team_approach": false,
    "stream_updates": true
  }')

# Extract the request ID and stream URL
REQUEST_ID=$(echo $RESPONSE | grep -o '"request_id":"[^"]*' | cut -d'"' -f4)
STREAM_URL=$(echo $RESPONSE | grep -o '"stream_url":"[^"]*' | cut -d'"' -f4)

echo "Request ID: $REQUEST_ID"
echo "Stream URL: $STREAM_URL"
echo ""
echo "Now watching the stream (Ctrl+C to stop):"
echo "----------------------------------------"

# If we got a stream URL, start watching it
if [ ! -z "$STREAM_URL" ]; then
  # Use curl with -N to disable buffering to see real-time updates
  curl -N "http://localhost:8000$STREAM_URL" -H "X-API-Key: test_key"
else
  echo "No stream URL received."
fi 