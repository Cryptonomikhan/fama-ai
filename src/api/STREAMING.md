# Streaming API

The Financial Modeling API supports real-time streaming of results using Server-Sent Events (SSE), providing a responsive and interactive experience for users.

## Overview

Instead of waiting for the entire financial model to be completed (which can take significant time), the streaming API sends progress updates and partial results as they become available. This allows applications to:

- Display real-time progress indicators
- Show intermediate results as they are generated
- Provide responsive feedback to users
- Handle long-running processes more gracefully

## How It Works

1. The client makes a request to the `/api/model` endpoint with `stream: true` in the request body
2. The server responds with a stream of Server-Sent Events (SSE)
3. Each event contains JSON data with information about the current progress
4. The client processes these events in real-time to update the UI

## Event Types

The streaming API emits the following event types:

### 1. Start Event

Sent when the processing begins:

```json
{
  "event": "start",
  "request_id": "uuid-string",
  "message": "Starting financial modeling process"
}
```

### 2. Progress Event

Sent during processing to indicate progress:

```json
{
  "event": "progress",
  "request_id": "uuid-string",
  "agent": "searcher",
  "message": "Running search agent",
  "progress": 10,
  "data": {
    "optional_intermediate_data": "value"
  }
}
```

### 3. Complete Event

Sent when processing is complete:

```json
{
  "event": "complete",
  "request_id": "uuid-string",
  "message": "Financial modeling complete",
  "data": {
    "request_id": "uuid-string",
    "search_results": "...",
    "assumptions": { ... },
    "metrics": [ ... ],
    "financial_model": { ... }
  },
  "progress": 100
}
```

### 4. Error Event

Sent when an error occurs:

```json
{
  "event": "error",
  "request_id": "uuid-string",
  "error": "Error message"
}
```

## Using the Streaming API

### Example Request

```bash
curl -X POST http://localhost:8000/api/model \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-api-key" \
  -d '{
    "description": "A tokenized real estate fund that invests in multifamily properties...",
    "provider": "formation",
    "stream": true
  }'
```

### Example Client Implementation

We provide a Python example client in `examples/streaming_client.py`:

```python
from sseclient import SSEClient
import requests
import json

url = "http://localhost:8000/api/model"
headers = {
    "Content-Type": "application/json",
    "x-api-key": "your-api-key"
}
payload = {
    "description": "Your investment description",
    "provider": "formation",
    "stream": True
}

response = requests.post(url, json=payload, headers=headers, stream=True)
client = SSEClient(response)

for event in client.events():
    data = json.loads(event.data)
    event_type = data.get("event")
    
    if event_type == "start":
        print(f"Started: {data.get('message')}")
    
    elif event_type == "progress":
        print(f"Progress: {data.get('progress')}% - {data.get('message')}")
    
    elif event_type == "complete":
        print(f"Completed: {data.get('message')}")
        final_result = data.get("data")
        print(f"Final result received with {len(final_result)} fields")
    
    elif event_type == "error":
        print(f"Error: {data.get('error')}")
```

### Frontend Implementation

For frontend applications, you can use the standard EventSource API:

```javascript
const eventSource = new EventSource('/api/model');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch(data.event) {
    case 'start':
      console.log(`Started: ${data.message}`);
      break;
    
    case 'progress':
      updateProgressBar(data.progress);
      console.log(`${data.message} - ${data.progress}%`);
      break;
    
    case 'complete':
      console.log('Model complete');
      displayResults(data.data);
      eventSource.close();
      break;
    
    case 'error':
      console.error(`Error: ${data.error}`);
      eventSource.close();
      break;
  }
};

eventSource.onerror = (error) => {
  console.error('EventSource error:', error);
  eventSource.close();
};
```

## Benefits of Streaming

1. **Improved User Experience**: Users don't have to wait for the entire process to complete before seeing results
2. **Real-time Feedback**: Progress indicators show exactly what's happening
3. **Error Handling**: Errors are communicated immediately
4. **Resource Efficiency**: Long-running processes don't block the server
5. **Graceful Degradation**: If connection is lost, the client still has partial results 