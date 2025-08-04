#!/bin/bash
# Clear environment and start expo
unset DB_HOST DB_PORT DB_NAME DB_USER DB_PASS PYTHONPATH
exec npx expo start --clear
