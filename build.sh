#!/bin/bash

echo "Starting deployment setup..."

# Database migration
echo "Running database migrations..."
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print('Database initialized!')"

echo "Deployment setup completed!"
