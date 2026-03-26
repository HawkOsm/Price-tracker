#!/bin/bash

# Setup script for Price Tracker on Ubuntu/Linux

APP_NAME="PriceTracker"
APP_DIR=$(pwd)
PYTHON_EXEC=$(which python3)
ICON_PATH="$APP_DIR/icon.png" # Assuming an icon exists or we use a default
DESKTOP_FILE="$HOME/.local/share/applications/price_tracker.desktop"

echo "Setting up $APP_NAME..."

# Create desktop entry
cat <<EOF > "$DESKTOP_FILE"
[Desktop Entry]
Version=1.0
Type=Application
Name=Price Tracker
Comment=Professional Product Price Tracker
Exec=$PYTHON_EXEC $APP_DIR/main.py
Path=$APP_DIR
Icon=utilities-terminal
Terminal=false
Categories=Utility;
EOF

chmod +x "$DESKTOP_FILE"

# Add to startup if requested
read -p "Do you want to start Price Tracker automatically on login? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    mkdir -p "$HOME/.config/autostart"
    cp "$DESKTOP_FILE" "$HOME/.config/autostart/"
    echo "Added to autostart."
fi

echo "Setup complete! You can find Price Tracker in your application menu."
