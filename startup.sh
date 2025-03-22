#!/bin/bash

# Navigate to the repository directory
cd "$(dirname "$0")" || exit 1

# Pull the latest changes
git pull origin main

# Store the current IP information
ip a > current_ip.txt

# Add, commit, and push the changes
git add current_ip.txt
git commit -m "Auto-update IP address on $(date)"
git push origin main
