# GUI.py
import sys

from PyQt5.QtCore import pyqtSlot, QThread, pyqtSignal, QTimer, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QApplication,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
    QMessageBox,
    QTableWidgetItem,
    QTableWidget,
    QHeaderView,
    QAbstractItemView,
    QProgressBar,
    QLabel,
    QSystemTrayIcon,
    QStyle,
)

from Product import Product, save_products, load_products
from Tracker import update_all_products


def _to_str(v):
    if v is None:
        return ""
    if isinstance(v, float):
        return f"{v:.2f}"
    return str(v)


class ScrapeWorker(QThread):
    progress = pyqtSignal(int, int, str, object)
    finished = pyqtSignal()

    def __init__(self, path="data.json"):
        super().__init__()
        self.path = path

    def run(self):
        update_all_products(self.path, callback=self.report_progress)
        self.finished.emit()

    def report_progress(self, current, total, name, price):
        self.progress.emit(current, total, name, price)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.products: list[Product] = []
        self.setWindowTitle("🛒 Product Price Tracker")
        self.setGeometry(200, 200, 1100, 600)

        self.InitUI()
        self.InitTray()
        self.load_from_json()
        
        # Start initial scrape in background
        self.refresh_prices()

        # Setup periodic refresh (every hour)
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_prices)
        self.timer.start(3600000)

    def InitTray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_ComputerIcon))
        self.tray_icon.show()

    def InitUI(self):
        # Input area
        self.name_box = QLineEdit()
        self.name_box.setPlaceholderText("Product Name")

        self.url_box = QLineEdit()
        self.url_box.setPlaceholderText("Product URL")

        self.selector_box = QLineEdit()
        self.selector_box.setPlaceholderText("CSS Selector (Optional)")

        self.add_button = QPushButton("➕ Add Product")
        self.add_button.clicked.connect(self.add_click)
        self.add_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")

        self.remove_button = QPushButton("🗑️ Remove Selected")
        self.remove_button.clicked.connect(self.remove_selected)

        self.refresh_button = QPushButton("🔄 Refresh Prices")
        self.refresh_button.clicked.connect(self.refresh_prices)

        # Table area
        self.product_table = QTableWidget()
        self.product_table.setColumnCount(5)
        self.product_table.setHorizontalHeaderLabels(
            ["Product Name", "Product URL", "Current Price", "Change %", "Max Diff"]
        )
        self.product_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.product_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.product_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        
        self.product_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.product_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.product_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.product_table.setAlternatingRowColors(True)

        # Layouts
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("Name:"))
        input_layout.addWidget(self.name_box)
        input_layout.addWidget(QLabel("URL:"))
        input_layout.addWidget(self.url_box)
        input_layout.addWidget(QLabel("Selector:"))
        input_layout.addWidget(self.selector_box)
        input_layout.addWidget(self.add_button)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.remove_button)
        button_layout.addStretch()
        button_layout.addWidget(self.refresh_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)

        main_layout = QVBoxLayout()
        main_layout.addLayout(input_layout)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(self.product_table)
        main_layout.addWidget(self.progress_bar)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.statusBar().showMessage("Ready")

    def load_from_json(self):
        self.products = load_products()
        self.update_table()

    def update_table(self):
        self.product_table.setRowCount(0)
        for p in self.products:
            row = self.product_table.rowCount()
            self.product_table.insertRow(row)
            
            # Name
            self.product_table.setItem(row, 0, QTableWidgetItem(p.get_name()))
            
            # URL
            url_item = QTableWidgetItem(p.get_url())
            url_item.setForeground(QColor("blue"))
            self.product_table.setItem(row, 1, url_item)
            
            # Current Price
            curr = p.get_current()
            self.product_table.setItem(row, 2, QTableWidgetItem(_to_str(curr)))
            
            # Change % (Positive means price dropped, Negative means increased in original implementation)
            change = p.get_change()
            change_item = QTableWidgetItem(f"{change}%")
            if change > 0:
                change_item.setForeground(QColor("green")) # Price dropped
            elif change < 0:
                change_item.setForeground(QColor("red")) # Price increased
            self.product_table.setItem(row, 3, change_item)
            
            # Max Diff
            self.product_table.setItem(row, 4, QTableWidgetItem(_to_str(p.get_max_change())))

    @pyqtSlot()
    def add_click(self):
        name = self.name_box.text().strip()
        url = self.url_box.text().strip()
        selector = self.selector_box.text().strip() or None

        if not name or not url:
            QMessageBox.warning(self, "Missing fields", "Please enter at least name and URL.")
            return

        product = Product(name, url, selector=selector)
        self.products.append(product)
        save_products(self.products)
        
        self.update_table()
        self.name_box.clear()
        self.url_box.clear()
        self.selector_box.clear()
        
        self.refresh_prices()

    def remove_selected(self):
        selected = self.product_table.selectionModel().selectedRows()
        if not selected:
            return

        if QMessageBox.question(self, "Confirm", "Delete selected products?", 
                                QMessageBox.Yes | QMessageBox.No) != QMessageBox.Yes:
            return

        rows = sorted([idx.row() for idx in selected], reverse=True)
        for r in rows:
            self.products.pop(r)
        
        save_products(self.products)
        self.update_table()

    def refresh_prices(self):
        if hasattr(self, 'worker') and self.worker.isRunning():
            return

        self.add_button.setEnabled(False)
        self.refresh_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.statusBar().showMessage("Updating prices...")

        self.worker = ScrapeWorker()
        self.worker.progress.connect(self.on_scrape_progress)
        self.worker.finished.connect(self.on_scrape_finished)
        self.worker.start()

    def on_scrape_progress(self, current, total, name, price):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.statusBar().showMessage(f"Updating {name}...")

    def on_scrape_finished(self):
        old_prices = {p.name: p.get_current() for p in self.products}
        self.load_from_json()
        
        # Check for price changes and notify
        for p in self.products:
            old_p = old_prices.get(p.name)
            new_p = p.get_current()
            if old_p and new_p and old_p != new_p:
                if new_p < old_p:
                    self.tray_icon.showMessage(
                        "Price Drop! 💸",
                        f"{p.name} dropped from {old_p} to {new_p}!",
                        QSystemTrayIcon.Information,
                        5000
                    )
                else:
                    self.tray_icon.showMessage(
                        "Price Increase 📈",
                        f"{p.name} rose from {old_p} to {new_p}.",
                        QSystemTrayIcon.Information,
                        5000
                    )

        self.add_button.setEnabled(True)
        self.refresh_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.statusBar().showMessage("Update complete", 5000)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
