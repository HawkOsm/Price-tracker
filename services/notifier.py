import os
import platform
import subprocess
import logging
from utils.helpers import setup_logger

logger = setup_logger(__name__)

class Notifier:
    @staticmethod
    def notify(title: str, message: str):
        """Send a desktop notification."""
        logger.info(f"Notification: {title} - {message}")
        
        system = platform.system()
        try:
            if system == "Linux":
                subprocess.run(["notify-send", title, message], check=False)
            elif system == "Windows":
                # Fallback for Windows if plyer/win10toast not installed
                # In a real app, we'd use a library.
                pass
            elif system == "Darwin": # macOS
                subprocess.run(["osascript", "-e", f'display notification "{message}" with title "{title}"'], check=False)
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
