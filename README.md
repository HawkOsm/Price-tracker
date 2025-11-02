# 🛒 Product Price Tracker

This is a simple **Python-based price tracking application** with a GUI built using **PyQt5** and Excel integration via **xlsxwriter** and **openpyxl**.
It allows you to:

* Add product names and URLs via a user-friendly GUI
* Automatically save them into an Json file
* Periodically fetch current prices from each URL and update them in json

---

## ⚙️ Features

* **GUI (PyQt5):**
  Add product name + URL easily.
* **Excel logging:**
  Saves all data to json automatically.
* **Web scraping:**
  Fetches the latest price from each product page using `requests` and `BeautifulSoup`.
* **Auto-update function:**
  With on_opem.py the preferd products will updated an notify user on change
  

---


## 🖥️ Requirements

Install these Python packages before running:

```bash
pip install PyQt5 openpyxl xlsxwriter requests beautifulsoup4 lxml
```

## 🧠 Technical Details


* **`GUI.py`**

  * Built with PyQt5
  * Uses `QTableWidget` to display products
  * Gracefully closes workbook on app exit

* **`Tracker.py`**

  * Scrapes price info using `requests` + `BeautifulSoup`
  * Automatically updates latest prices

---

## 💡 Notes & Recommendations

* **Respect websites’ terms of service.**
  Do not scrape aggressively or too frequently.
* **Add delay between requests** (`delay_s` parameter in `Tracker.py`) to avoid rate limits.
* **If pages require JavaScript rendering** (e.g., dynamic prices), consider using `Selenium` or `Playwright`.
* **Backup your Excel file** occasionally — each run updates prices in place.
* **Optional startup automation:**
  You can schedule `Tracker.py` with **Windows Task Scheduler** or `crontab` to auto-run daily.

---

## 📜 License

This mini project is for **educational and personal use**.
You are free to modify and extend it.

---
