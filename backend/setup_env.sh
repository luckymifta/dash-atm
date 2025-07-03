#!/bin/bash
# Helper script to create a proper .env file from .env.example

# Define colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}ATM Dashboard .env Configuration Helper${NC}"
echo -e "${YELLOW}========================================${NC}"

# Check if .env file already exists
if [ -f .env ]; then
  echo -e "${YELLOW}An existing .env file was found.${NC}"
  read -p "Do you want to overwrite it? (y/N) " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Operation cancelled. Existing .env file preserved.${NC}"
    exit 0
  fi
fi

# Check if .env.example exists
if [ ! -f .env.example ]; then
  echo -e "${RED}Error: .env.example file not found.${NC}"
  exit 1
fi

# Copy .env.example to .env
cp .env.example .env
if [ $? -ne 0 ]; then
  echo -e "${RED}Failed to create .env file. Please check file permissions.${NC}"
  exit 1
fi

echo -e "${GREEN}Created new .env file from template.${NC}"
echo -e "${YELLOW}Please enter your database connection details:${NC}"

# Get database connection details
read -p "Database Host [localhost]: " db_host
db_host=${db_host:-localhost}

read -p "Database Port [5432]: " db_port
db_port=${db_port:-5432}

read -p "Database Name [atm_database]: " db_name
db_name=${db_name:-atm_database}

read -p "Database User [postgres]: " db_user
db_user=${db_user:-postgres}

read -p "Database Password: " db_password

# Update .env file with entered values
sed -i.bak "s/DB_HOST=.*/DB_HOST=$db_host/" .env
sed -i.bak "s/DB_PORT=.*/DB_PORT=$db_port/" .env
sed -i.bak "s/DB_NAME=.*/DB_NAME=$db_name/" .env
sed -i.bak "s/DB_USER=.*/DB_USER=$db_user/" .env
sed -i.bak "s/DB_PASSWORD=.*/DB_PASSWORD=$db_password/" .env

# Remove backup file
rm -f .env.bak

echo -e "${GREEN}Database connection details updated in .env file.${NC}"
echo -e "${YELLOW}----------------------------------------${NC}"
echo -e "${YELLOW}To verify database connection, run:${NC}"
echo -e "${GREEN}python verify_env_loading.py${NC}"
echo
echo -e "${YELLOW}To test database connection, run:${NC}"
echo -e "${GREEN}python test_db_connection.py${NC}"
echo -e "${YELLOW}----------------------------------------${NC}"
