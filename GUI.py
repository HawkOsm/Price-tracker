# GUI.py
import sys

from PyQt5.QtCore import pyqtSlot
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
)

from Product import Product, save_products, load_products
from Queue import CircularQueue
from Tracker import update_all_products


def _to_str(v):
    return "" if v is None else str(v)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.products: list[Product] = []
        self.setWindowTitle("Products")
        self.setGeometry(200, 200, 1000, 500)

        self.InitUI()
        # JSON only: load what we have
        self.load_from_json()
        # Optional: scrape immediately, then refresh UI
        update_all_products("data.json")
        self.load_from_json()

    def InitUI(self):
        self.name_box = QLineEdit()
        self.name_box.setPlaceholderText("Enter The Product Name")

        self.url_box = QLineEdit()
        self.url_box.setPlaceholderText("Enter The Product URL")

        self.add_button = QPushButton("Add Product", self)
        self.add_button.clicked.connect(self.add_click)

        self.remove_button = QPushButton("Remove Selected", self)
        self.remove_button.clicked.connect(self.remove_selected)

        self.refresh_button = QPushButton("Refresh Prices", self)
        self.refresh_button.clicked.connect(self.refresh_prices)

        self.product_table = QTableWidget()
        self.product_table.setColumnCount(5)
        self.product_table.setHorizontalHeaderLabels(
            ["Product Name", "Product URL", "Current Price", "Change", "Max Change"]
        )
        self.product_table.horizontalHeader().setStretchLastSection(True)
        self.product_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.product_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.product_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.product_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        info_layout = QHBoxLayout()
        info_layout.addWidget(self.name_box)
        info_layout.addWidget(self.url_box)
        info_layout.addWidget(self.add_button)
        info_layout.addWidget(self.remove_button)
        info_layout.addWidget(self.refresh_button)

        list_layout = QHBoxLayout()
        list_layout.addWidget(self.product_table)

        main_layout = QVBoxLayout()
        main_layout.addLayout(info_layout)
        main_layout.addLayout(list_layout)

        container = QWidget(self)
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def load_from_json(self):
        self.products = load_products()
        self.product_table.setRowCount(0)
        for p in self.products:
            row = self.product_table.rowCount()
            self.product_table.insertRow(row)
            self.product_table.setItem(row, 0, QTableWidgetItem(_to_str(p.get_name())))
            self.product_table.setItem(row, 1, QTableWidgetItem(_to_str(p.get_url())))
            self.product_table.setItem(row, 2, QTableWidgetItem(_to_str(p.get_current())))
            self.product_table.setItem(row, 3, QTableWidgetItem(_to_str(p.get_change())))
            self.product_table.setItem(row, 4, QTableWidgetItem(_to_str(p.get_max_change())))

    @pyqtSlot()
    def add_click(self):
        name = self.name_box.text().strip()
        url = self.url_box.text().strip()

        if not name:
            QMessageBox.warning(self, "Missing name", "Please enter the product name.")
            return
        if not url:
            QMessageBox.warning(self, "Missing URL", "Please enter the product URL.")
            return

        queue = CircularQueue(30)
        product = Product(name, url, queue)
        self.products.append(product)

        # Persist immediately (prevents losing data on crash)
        self.save_products_to_json()

        # Scrape & refresh UI
        update_all_products("data.json")
        self.load_from_json()

        self.name_box.clear()
        self.url_box.clear()

    def remove_selected(self):
        model = self.product_table.selectionModel()
        selected = model.selectedRows() if model else []

        if not selected:
            QMessageBox.information(self, "No Selection", "Please select at least one row to remove.")
            return

        rows = sorted([idx.row() for idx in selected], reverse=True)
        confirm = QMessageBox.question(
            self, "Confirm Deletion",
            f"Are you sure you want to delete {len(rows)} product(s)?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        # Remove from in-memory list and table
        for r in rows:
            if 0 <= r < len(self.products):
                self.products.pop(r)
            self.product_table.removeRow(r)

        # Persist the new list (IMPORTANT — this was missing)
        self.save_products_to_json()

    def refresh_prices(self):
        update_all_products("data.json")
        self.load_from_json()

    def save_products_to_json(self):
        # Never pass None; always a list (even empty).
        # If you DON’T want to allow wiping file when empty, early return here.
        # if not self.products: return
        save_products(self.products)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
