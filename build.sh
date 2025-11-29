#!/bin/bash

echo "Starting deployment setup..."

# Database migration
echo "Running database migrations..."
python -c "
from app import create_app, db
from app.models.user import User
from sqlalchemy import text

app = create_app()
app.app_context().push()

# Add word file columns if they don't exist
try:
    with db.engine.connect() as conn:
        conn.execute(text('ALTER TABLE reports ADD COLUMN IF NOT EXISTS word_file_path VARCHAR(255)'))
        conn.execute(text('ALTER TABLE reports ADD COLUMN IF NOT EXISTS word_file_size INTEGER'))
        conn.commit()
    print('Word file columns added/verified!')
except Exception as e:
    print(f'Migration note: {e}')

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
