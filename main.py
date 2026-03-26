import sys
import asyncio
from qasync import QEventLoop
from PyQt6.QtWidgets import QApplication
from qt_material import apply_stylesheet

from ui.main_window import MainWindow
from core.migration import initialize_database, migrate_from_json
from utils.helpers import setup_logger

logger = setup_logger(__name__)

async def main():
    logger.info("Starting Price Tracker Application...")
    
    # Initialize DB and Migrate
    initialize_database()
    migrate_from_json("data.json")
    
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    # Apply modern theme
    apply_stylesheet(app, theme='dark_teal.xml')
    
    window = MainWindow()
    window.show()
    
    with loop:
        loop.run_forever()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"Application crashed: {e}")
