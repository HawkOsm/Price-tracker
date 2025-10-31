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
)
from PyQt5.QtWidgets import QAbstractItemView

from ToExcell import excel, read_all, ensure_workbook


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Products")
        self.setGeometry(200, 200, 1000, 500)

        self.InitUI()

        # Ensure workbook exists and load existing rows
        ensure_workbook()
        self.load_from_xlsx()

    def InitUI(self):
        self.name_box = QLineEdit()
        self.name_box.setPlaceholderText("Enter The Product Name")

        self.url_box = QLineEdit()
        self.url_box.setPlaceholderText("Enter The Product URL")

        self.add_button = QPushButton("Add Product", self)
        self.add_button.clicked.connect(self.add_click)

        # NEW: Remove button
        self.remove_button = QPushButton("Remove Selected", self)
        self.remove_button.clicked.connect(self.remove_selected)

        # Table with 2 columns
        self.product_table = QTableWidget()
        self.product_table.setColumnCount(5)
        self.product_table.setHorizontalHeaderLabels(["Product Name", "Product URL","Current Price","Daily Change","Max Change"])
        self.product_table.horizontalHeader().setStretchLastSection(True)
        self.product_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        # Better selection UX for row deletion
        self.product_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.product_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.product_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        # Layouts
        info_layout = QHBoxLayout()
        info_layout.addWidget(self.name_box)
        info_layout.addWidget(self.url_box)
        info_layout.addWidget(self.add_button)
        info_layout.addWidget(self.remove_button)  # add the Remove button to the toolbar

        list_layout = QHBoxLayout()
        list_layout.addWidget(self.product_table)

        main_layout = QVBoxLayout()
        main_layout.addLayout(info_layout)
        main_layout.addLayout(list_layout)

        container = QWidget(self)
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def load_from_xlsx(self):
        """Load all existing rows from products.xlsx into the table."""
        self.product_table.setRowCount(0)
        for name, url in read_all():
            row_position = self.product_table.rowCount()
            self.product_table.insertRow(row_position)
            self.product_table.setItem(row_position, 0, QTableWidgetItem(name or ""))
            self.product_table.setItem(row_position, 1, QTableWidgetItem(url or ""))

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

        # 1) Persist immediately to products.xlsx
        try:
            excel(name, url)
        except Exception as e:
            QMessageBox.critical(self, "Save error", f"Could not write to Excel:\n{e}")
            return

        # 2) Append to UI table
        row_position = self.product_table.rowCount()
        self.product_table.insertRow(row_position)
        self.product_table.setItem(row_position, 0, QTableWidgetItem(name))
        self.product_table.setItem(row_position, 1, QTableWidgetItem(url))

        # 3) Clear inputs
        self.name_box.clear()
        self.url_box.clear()

    # =========================
    # NEW: Remove functionality
    # =========================
    def remove_selected(self):
        """Remove selected rows from the table and rewrite products.xlsx."""
        model = self.product_table.selectionModel()
        selected = model.selectedRows() if model else []

        if not selected:
            QMessageBox.information(self, "No Selection", "Please select at least one row to remove.")
            return

        rows = sorted([idx.row() for idx in selected], reverse=True)

        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete {len(rows)} product(s)?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return

        # Remove from table (from bottom to top to keep indices valid)
        for r in rows:
            self.product_table.removeRow(r)

        # Rewrite Excel to mirror the current table
        try:
            self.save_table_to_excel()
        except Exception as e:
            QMessageBox.critical(self, "Excel Error", f"Failed to update products.xlsx:\n{e}")

    def save_table_to_excel(self):
        """Rewrite products.xlsx from the current table contents."""
        from openpyxl import Workbook

        wb = Workbook()
        ws = wb.active
        ws.title = "Products"
        # Keep header compatible with Tracker.py and ToExcell.py
        ws.append(["Item", "URL", "Price"])

        for row in range(self.product_table.rowCount()):
            name_item = self.product_table.item(row, 0)
            url_item = self.product_table.item(row, 1)
            name = name_item.text() if name_item else ""
            url = url_item.text() if url_item else ""
            ws.append([name, url, None])

        wb.save("products.xlsx")
        wb.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
