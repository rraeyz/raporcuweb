#!/bin/bash

echo "Starting deployment setup..."

# Database migration with Flask-Migrate
echo "Running database migrations..."
flask db upgrade

echo "Deployment setup completed!"
