# 🛒 Professional Product Price Tracker

A professional-grade price tracking application with a modern GUI, asynchronous scraper, and persistent SQLite database.

## ⚙️ Features
- **Modern UI (PyQt6 + qt-material):** Professional dark theme, interactive tables, and integrated price history graphs (Matplotlib).
- **Asynchronous Scraper (httpx):** High-performance scraping with support for international currency formats and custom CSS selectors.
- **Persistent Storage (SQLAlchemy):** SQLite-backed database to track long-term price trends and multiple products efficiently.
- **Background Automation (APScheduler):** Automatic periodic price checks with desktop notifications.
- **Ubuntu/Linux Integration:** Easy setup with systemd/desktop integration script.
- **Clean Code Architecture:** Modular design following professional standards.

## 🧠 Technical Details
### Project Structure
- `/core`: Scraper logic (`scraper.py`), Database models (`models.py`), and Database configuration (`database.py`).
- `/ui`: PyQt6 interface (`main_window.py`).
- `/services`: Background scheduler (`scheduler.py`) and Notification logic (`notifier.py`).
- `/utils`: Common helpers and logger setup (`helpers.py`).
- `main.py`: Main application entry point.

## 🚀 Getting Started
### Prerequisites
Ensure you have the required dependencies:
```bash
pip install sqlalchemy httpx apscheduler qt-material pyqt6 matplotlib qasync beautifulsoup4 lxml
```

### Installation & Run
1. Run the application:
   ```bash
   python3 main.py
   ```
2. For Ubuntu integration:
   ```bash
   chmod +x setup_service.sh
   ./setup_service.sh
   ```

## 📜 Notes
- Always respect websites' terms of service.
- Use custom CSS selectors for unsupported sites for more accurate scraping.

## 📜 License
Educational and personal use.
