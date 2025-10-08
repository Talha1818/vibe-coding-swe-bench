#!/bin/bash
# Docker install script for Amazon Linux 2023

set -e

echo "🔄 Updating system..."
sudo dnf update -y

echo "🐳 Installing Docker..."
sudo dnf install -y docker

echo "⚙️ Enabling Docker service..."
sudo systemctl enable docker
sudo systemctl start docker

echo "👤 Adding ec2-user to docker group..."
sudo usermod -aG docker ec2-user

echo "✅ Docker installed successfully!"
echo "👉 Run 'newgrp docker' or log out and back in to use Docker without sudo."
docker --version


