import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from core.database import SessionLocal
from core.models import ProductModel, PriceHistoryModel
from core.scraper import fetch_price
from services.notifier import Notifier
from utils.helpers import setup_logger

logger = setup_logger(__name__)

class PriceScheduler:
    def __init__(self, interval_hours: int = 1):
        self.scheduler = AsyncIOScheduler()
        self.interval_hours = interval_hours
        self._is_running = False

    async def check_all_prices(self):
        """Scrape all products and save history."""
        logger.info("Background price check started.")
        db = SessionLocal()
        try:
            products = db.query(ProductModel).all()
            for product in products:
                _, price = await fetch_price(product.url, product.selector)
                if price is not None:
                    # Get last price
                    last_history = db.query(PriceHistoryModel).filter(
                        PriceHistoryModel.product_id == product.id
                    ).order_by(PriceHistoryModel.timestamp.desc()).first()
                    
                    if last_history:
                        old_price = last_history.price
                        if price < old_price:
                            Notifier.notify("Price Drop!", f"{product.name} dropped from {old_price} to {price}!")
                        elif price > old_price:
                            Notifier.notify("Price Rise!", f"{product.name} increased from {old_price} to {price}!")
                    
                    # Save new price
                    history = PriceHistoryModel(product_id=product.id, price=price)
                    db.add(history)
            
            db.commit()
            logger.info("Background price check completed.")
        except Exception as e:
            db.rollback()
            logger.error(f"Error in background check: {e}")
        finally:
            db.close()

    def start(self):
        if not self._is_running:
            self.scheduler.add_job(self.check_all_prices, 'interval', hours=self.interval_hours)
            self.scheduler.start()
            self._is_running = True
            logger.info(f"Scheduler started with {self.interval_hours}h interval.")

    def stop(self):
        if self._is_running:
            self.scheduler.shutdown()
            self._is_running = False
            logger.info("Scheduler stopped.")
