#!/bin/bash

echo "Container is running!!!"

# Function to run the Uvicorn server for development
uvicorn_server() {
    python -m uvicorn api.service:app --host 0.0.0.0 --port 9000 --timeout-keep-alive 5000 --log-level debug --reload --reload-dir api/ "$@"
}

# Function to run the Uvicorn server for production
uvicorn_server_production() {
    python -m uvicorn api.service:app --host 0.0.0.0 --port 9000 --timeout-keep-alive 5000 --lifespan on
}

export -f uvicorn_server
export -f uvicorn_server_production

echo -en "\033[92m
The following commands are available:
    uvicorn_server
        Run the Uvicorn Server
\033[0m
"

# Check if in development mode and choose the appropriate server function
if [ "${DEV}" = "1" ]; then
  uvicorn_server
else
  uvicorn_server_production
fi
