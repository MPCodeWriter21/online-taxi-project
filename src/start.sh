#!/bin/bash
echo "Starting the app...";

# Run migrations
echo "Running database migrations..."
poetry run migrate-db

if [[ -z $DEBUG ]] || [[ $DEBUG == "false" ]]; then
    echo "Starting production server..."
    poetry run poe prod;
else
    echo "Starting development server..."
    poetry run poe dev;
fi
