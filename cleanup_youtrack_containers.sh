#!/bin/bash
# Clean up any leftover YouTrack MCP containers
docker ps -aq --filter "ancestor=windbit/agentek-youtrack-mcp" | xargs -r docker rm -f
echo "Cleaned up YouTrack MCP containers"
