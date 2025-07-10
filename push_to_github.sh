#!/bin/bash

# Git Push Script for ATM Database Schema Updates
# This script commits and pushes the changes to a specific branch on GitHub

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}====================================================${NC}"
echo -e "${BLUE}   Git Push Script for ATM Database Schema Updates   ${NC}"
echo -e "${BLUE}====================================================${NC}"

# Ask for the branch name if not provided
read -p "Enter the branch name to push to: " BRANCH_NAME

# Check if branch name is provided
if [ -z "$BRANCH_NAME" ]; then
    echo -e "${YELLOW}No branch name provided. Using 'db-schema-updates' as default.${NC}"
    BRANCH_NAME="db-schema-updates"
fi

echo -e "${GREEN}Starting git operations for branch: ${BRANCH_NAME}${NC}"

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    cd ..
    if [ ! -d ".git" ]; then
        echo -e "${YELLOW}Not in a git repository. Please navigate to the repository root.${NC}"
        exit 1
    fi
fi

# Check if the branch exists locally
if ! git show-ref --verify --quiet refs/heads/$BRANCH_NAME; then
    echo -e "${YELLOW}Branch $BRANCH_NAME doesn't exist locally. Creating it...${NC}"
    git checkout -b $BRANCH_NAME
else
    echo -e "${GREEN}Switching to branch $BRANCH_NAME...${NC}"
    git checkout $BRANCH_NAME
fi

# Add the modified files
echo -e "${GREEN}Adding modified files...${NC}"
git add backend/atm_database.py
git add backend/test_db_tables.py
git add backend/DATABASE_SCHEMA_ANALYSIS.md
git add backend/DATABASE_SCHEMA_UPDATE_SUMMARY.md
git add backend/check_db_schema_extended.py
git add backend/run_continuous_with_cash.bat
git add backend/run_continuous_with_cash.ps1
git add backend/WINDOWS_OPERATION_GUIDE.md

# Commit the changes
echo -e "${GREEN}Committing changes...${NC}"
git commit -m "Update database schema to use regional_data and terminal_cash_information tables"

# Push to the remote repository
echo -e "${GREEN}Pushing to remote repository...${NC}"
git push origin $BRANCH_NAME

echo -e "${GREEN}Done! Changes pushed to branch $BRANCH_NAME${NC}"
echo -e "${YELLOW}You can now pull these changes on your Windows machine using:${NC}"
echo -e "git checkout $BRANCH_NAME"
echo -e "git pull origin $BRANCH_NAME"
