import json
import os
from datetime import datetime, timedelta
from core.database import Base, engine, SessionLocal
from core.models import ProductModel, PriceHistoryModel

def initialize_database():
    Base.metadata.create_all(bind=engine)

def migrate_from_json(json_path="data.json"):
    if not os.path.exists(json_path):
        print(f"No {json_path} found, skipping migration.")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print(f"Error decoding {json_path}, skipping migration.")
            return

    db = SessionLocal()
    try:
        for item in data:
            name = item.get("name")
            url = item.get("url")
            selector = item.get("selector")
            values = item.get("values", [])

            # Create product
            product = ProductModel(name=name, url=url, selector=selector)
            db.add(product)
            db.flush()  # To get product.id

            # Add price history (assuming they were added daily, backwards from now)
            now = datetime.utcnow()
            for i, price in enumerate(reversed(values)):
                history = PriceHistoryModel(
                    product_id=product.id,
                    price=float(price),
                    timestamp=now - timedelta(days=i)
                )
                db.add(history)
        
        db.commit()
        print(f"Successfully migrated {len(data)} products from {json_path}.")
    except Exception as e:
        db.rollback()
        print(f"Error during migration: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    initialize_database()
    migrate_from_json()
