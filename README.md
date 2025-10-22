Here’s a professional **README.md** for your mini project — it explains setup, usage, and purpose clearly, based on your files (`GUI.py`, `ToExcell.py`, `Tracker.py`, and `products.xlsx`).

---

# 🛒 Product Price Tracker (Mini Project)

This is a simple **Python-based price tracking application** with a GUI built using **PyQt5** and Excel integration via **xlsxwriter** and **openpyxl**.
It allows you to:

* Add product names and URLs via a user-friendly GUI
* Automatically save them into an Excel file (`products.xlsx`)
* Periodically fetch current prices from each URL and update them in Excel

---

## ⚙️ Features

* **GUI (PyQt5):**
  Add product name + URL easily.
* **Excel logging:**
  Saves all data to `products.xlsx` automatically.
* **Web scraping:**
  Fetches the latest price from each product page using `requests` and `BeautifulSoup`.
* **Auto-update function:**
  You can run `Tracker.py` to refresh all product prices in one click.

---

## 🧩 Project Structure

```
📁 ProductPriceTracker
├── GUI.py              # Main PyQt5 interface
├── ToExcell.py         # Handles writing new products to Excel
├── Tracker.py          # Reads Excel & updates prices from websites
├── products.xlsx       # Generated automatically; stores product data
└── README.md
```

---

## 🖥️ Requirements

Install these Python packages before running:

```bash
pip install PyQt5 openpyxl xlsxwriter requests beautifulsoup4 lxml
```

---

## 🚀 How to Run

### 1️⃣ Start the GUI

```bash
python GUI.py
```

This opens a window where you can:

* Enter a **Product Name**
* Enter a **Product URL**
* Click **Add Product**

Each entry is saved to `products.xlsx` automatically.

---

### 2️⃣ Track Prices

To fetch and update product prices:

```bash
python Tracker.py
```

This script:

* Reads each URL from column **B** of `products.xlsx`
* Scrapes the current price (if found)
* Writes it to column **C** beside the product

---

## 🧠 Technical Details

* **`ToExcell.py`**
  Uses `xlsxwriter` to initialize and write to `products.xlsx`
  Columns:

  | A            | B   | C     |
  | ------------ | --- | ----- |
  | Product Name | URL | Price |

* **`GUI.py`**

  * Built with PyQt5
  * Uses `QTableWidget` to display products
  * Saves new entries through the `excel()` function from `ToExcell.py`
  * Gracefully closes workbook on app exit

* **`Tracker.py`**

  * Uses `openpyxl` to open `products.xlsx`
  * Scrapes price info using `requests` + `BeautifulSoup`
  * Automatically updates column `C` with the latest prices

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