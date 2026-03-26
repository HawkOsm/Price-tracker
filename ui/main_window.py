import asyncio
from datetime import datetime, timedelta
import logging

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel, QMessageBox,
    QSplitter, QProgressBar, QStatusBar
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QColor, QAction

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from qt_material import apply_stylesheet

from core.database import SessionLocal
from core.models import ProductModel, PriceHistoryModel
from core.scraper import fetch_price
from services.scheduler import PriceScheduler
from utils.helpers import setup_logger

logger = setup_logger(__name__)

class PriceGraph(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)

    def plot(self, timestamps, prices, product_name):
        self.axes.clear()
        self.axes.plot(timestamps, prices, marker='o', linestyle='-', color='teal')
        self.axes.set_title(f"Price History: {product_name}")
        self.axes.set_xlabel("Date")
        self.axes.set_ylabel("Price")
        self.axes.grid(True)
        self.fig.autofmt_xdate()
        self.draw()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🛒 Price Tracker")
        self.resize(1200, 800)

        # Initialize Scheduler
        self.scheduler = PriceScheduler(interval_hours=1)
        self.scheduler.start()

        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Input Area
        input_widget = QWidget()
        input_layout = QHBoxLayout(input_widget)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Product Name")
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Product URL")
        self.selector_input = QLineEdit()
        self.selector_input.setPlaceholderText("CSS Selector (Optional)")
        
        add_btn = QPushButton("Add Product")
        add_btn.clicked.connect(self.add_product)
        
        refresh_btn = QPushButton("Refresh All")
        refresh_btn.clicked.connect(self.refresh_all)
        
        input_layout.addWidget(QLabel("Name:"))
        input_layout.addWidget(self.name_input)
        input_layout.addWidget(QLabel("URL:"))
        input_layout.addWidget(self.url_input)
        input_layout.addWidget(QLabel("Selector:"))
        input_layout.addWidget(self.selector_input)
        input_layout.addWidget(add_btn)
        input_layout.addWidget(refresh_btn)
        
        main_layout.addWidget(input_widget)

        # Splitter for Table and Graph
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Product Name", "Current Price", "Last Updated"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemSelectionChanged.connect(self.selection_changed)
        
        splitter.addWidget(self.table)
        
        # Graph
        self.graph = PriceGraph(self, width=8, height=4)
        splitter.addWidget(self.graph)
        
        main_layout.addWidget(splitter)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # Status Bar
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready")

    def load_data(self):
        db = SessionLocal()
        try:
            products = db.query(ProductModel).all()
            self.table.setRowCount(len(products))
            for i, p in enumerate(products):
                self.table.setItem(i, 0, QTableWidgetItem(str(p.id)))
                self.table.setItem(i, 1, QTableWidgetItem(p.name))
                
                # Get last price
                last_history = db.query(PriceHistoryModel).filter(
                    PriceHistoryModel.product_id == p.id
                ).order_by(PriceHistoryModel.timestamp.desc()).first()
                
                if last_history:
                    self.table.setItem(i, 2, QTableWidgetItem(f"{last_history.price:.2f}"))
                    self.table.setItem(i, 3, QTableWidgetItem(last_history.timestamp.strftime("%Y-%m-%d %H:%M")))
                else:
                    self.table.setItem(i, 2, QTableWidgetItem("N/A"))
                    self.table.setItem(i, 3, QTableWidgetItem("Never"))
        finally:
            db.close()

    @pyqtSlot()
    def add_product(self):
        name = self.name_input.text().strip()
        url = self.url_input.text().strip()
        selector = self.selector_input.text().strip() or None
        
        if not name or not url:
            QMessageBox.warning(self, "Missing Data", "Please enter name and URL.")
            return
            
        db = SessionLocal()
        try:
            product = ProductModel(name=name, url=url, selector=selector)
            db.add(product)
            db.commit()
            self.name_input.clear()
            self.url_input.clear()
            self.selector_input.clear()
            self.load_data()
            self.statusBar().showMessage(f"Product '{name}' added.", 5000)
        except Exception as e:
            logger.error(f"Error adding product: {e}")
            db.rollback()
        finally:
            db.close()

    def selection_changed(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            return
        
        product_id = int(self.table.item(selected_items[0].row(), 0).text())
        product_name = self.table.item(selected_items[0].row(), 1).text()
        
        db = SessionLocal()
        try:
            history = db.query(PriceHistoryModel).filter(
                PriceHistoryModel.product_id == product_id
            ).order_by(PriceHistoryModel.timestamp.asc()).all()
            
            if history:
                timestamps = [h.timestamp for h in history]
                prices = [h.price for h in history]
                self.graph.plot(timestamps, prices, product_name)
        finally:
            db.close()

    @pyqtSlot()
    def refresh_all(self):
        asyncio.create_task(self.run_refresh())

    async def run_refresh(self):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.statusBar().showMessage("Refreshing prices...")
        
        db = SessionLocal()
        try:
            products = db.query(ProductModel).all()
            total = len(products)
            if total == 0:
                self.progress_bar.setVisible(False)
                return

            for i, p in enumerate(products):
                _, price = await fetch_price(p.url, p.selector)
                if price is not None:
                    history = PriceHistoryModel(product_id=p.id, price=price)
                    db.add(history)
                self.progress_bar.setValue(int(((i + 1) / total) * 100))
            
            db.commit()
            self.load_data()
            self.statusBar().showMessage("Refresh complete.", 5000)
        except Exception as e:
            logger.error(f"Error in manual refresh: {e}")
            db.rollback()
        finally:
            db.close()
            self.progress_bar.setVisible(False)

    def closeEvent(self, event):
        self.scheduler.stop()
        super().closeEvent(event)
