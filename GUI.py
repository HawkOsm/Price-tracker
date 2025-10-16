import sys

from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QPixmap, QTextItem
from PyQt5.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QSlider,
    QSpinBox, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QMessageBox, QTableWidgetItem, QTableWidget, QHeaderView,
)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Products")
        self.setGeometry(200,200,1000,500)
        self.InitUI()


    def InitUI(self):
        self.name_box=QLineEdit()
        self.name_box.setPlaceholderText("Enter The Product Name")

        self.url_box=QLineEdit()
        self.url_box.setPlaceholderText("Enter The Product URL")

        self.add_button= QPushButton("Add Product",self)
        self.add_button.clicked.connect(self.add_click)

        #  Create a table with 2 columns
        self.product_table = QTableWidget()
        self.product_table.setColumnCount(2)
        self.product_table.setHorizontalHeaderLabels(["Product Name", "Product URL"])
        self.product_table.horizontalHeader().setStretchLastSection(True)
        self.product_table.horizontalHeader().setStretchLastSection(True)
        self.product_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.info_layout= QHBoxLayout()
        self.info_layout.addWidget(self.name_box)
        self.info_layout.addWidget(self.url_box)
        self.info_layout.addWidget(self.add_button)

        self.list_layout=QHBoxLayout()
        self.list_layout.addWidget(self.product_table)

        self.main_layout=QVBoxLayout()
        self.main_layout.addLayout(self.info_layout)
        self.main_layout.addLayout(self.list_layout)

        self.layout= QWidget(self)
        self.layout.setLayout(self.main_layout)
        self.setCentralWidget(self.layout)

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

        row_position = self.product_table.rowCount()
        self.product_table.insertRow(row_position)
        self.product_table.setItem(row_position, 0, QTableWidgetItem(name))
        self.product_table.setItem(row_position, 1, QTableWidgetItem(url))


        # Optionally clear the inputs
        self.name_box.clear()
        self.url_box.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())