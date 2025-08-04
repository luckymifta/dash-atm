#!/bin/bash

# Set environment variables to disable code signing for iOS simulator
export CODE_SIGN_IDENTITY=""
export DEVELOPMENT_TEAM=""
export CODE_SIGN_STYLE="Manual"

# Navigate to project directory
cd "/Users/luckymifta/Documents/2. AREA/dash-atm/mobile-flutter"

# Run Flutter app on iOS simulator
flutter run -d "ACE2DD7A-7542-4E99-912F-53FCEFA63A18" --debug --verbose
