#!/bin/bash

echo "Starting deployment setup..."

# Database migration
echo "Running database migrations..."
python -c "
from app import create_app, db
from app.models.user import User

app = create_app()
app.app_context().push()

# Create all tables
db.create_all()
print('Database initialized!')

# Check if admin exists
admin = User.query.filter_by(username='admin').first()
if not admin:
    admin = User(username='admin', email='admin@example.com', is_admin=True)
    admin.set_password('Admin123!')
    db.session.add(admin)
    db.session.commit()
    print('Admin user created! Username: admin, Password: Admin123!')
else:
    print('Admin user already exists.')
"

echo "Deployment setup completed!"
