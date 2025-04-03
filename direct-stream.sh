#!/bin/bash

# Very simple script to test direct streaming endpoint

echo "Starting direct stream request (Ctrl+C to stop)..."
echo "----------------------------------------"

curl -N -X POST http://localhost:8000/api/submit/stream \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test_key" \
  -d '{
    "description": "A small real estate fund that invests in AI server farms.",
    "time_horizon": 3,
    "risk_factors": "moderate",
    "output_format": "json",
    "use_team_approach": false,
    "stream_updates": true
  }' 