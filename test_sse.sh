#!/bin/bash

# Test script to verify SSE streaming is working properly

echo "=== Testing Song Graph SSE Streaming ==="
echo ""

# Step 1: Get playlist with tracks
echo "Step 1: Fetching playlist with tracks..."
PLAYLIST_URL="https://open.spotify.com/playlist/6ENxgIEdvQK45A3sLIq6t0"
RESPONSE=$(curl -s "http://localhost:8000/api/playlist-with-tracks?playlist_url=$PLAYLIST_URL")

# Extract playlist name
PLAYLIST_NAME=$(echo $RESPONSE | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['playlist_name'])")
echo "✓ Playlist name: $PLAYLIST_NAME"

# Extract first track ID
TRACK_COUNT=$(echo $RESPONSE | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data['tracks']))")
echo "✓ Track count: $TRACK_COUNT"

# Step 2: Start feature processing
echo ""
echo "Step 2: Starting feature processing..."
JOB_RESPONSE=$(curl -s -X POST http://localhost:8000/api/process-features \
  -H "Content-Type: application/json" \
  -d "{\"tracks\": $(echo $RESPONSE | python3 -c "import sys, json; data=json.load(sys.stdin); print(json.dumps(data['tracks']))"), \"playlist_name\": \"$PLAYLIST_NAME\"}")

JOB_ID=$(echo $JOB_RESPONSE | python3 -c "import sys, json; print(json.loads(sys.stdin.read())['job_id'])")
echo "✓ Job ID: $JOB_ID"

# Step 3: Connect to SSE stream
echo ""
echo "Step 3: Connecting to SSE stream (showing first 50 events)..."
echo "---"
curl -s -N "http://localhost:8000/api/progress-stream/$JOB_ID" | head -n 50
echo "---"
echo ""
echo "✓ SSE stream test complete!"

