#!/bin/bash

echo "Starting deployment setup..."

# Install system packages
echo "Installing system packages..."
apt-get update
apt-get install -y texlive-xetex texlive-fonts-recommended texlive-latex-recommended texlive-latex-extra lmodern cm-super pandoc

# Verify XeLaTeX installation
echo "Verifying XeLaTeX..."
which xelatex || echo "WARNING: xelatex not found!"

# Database migration with Flask-Migrate
echo "Running database migrations..."
flask db upgrade

echo "Deployment setup completed!"
