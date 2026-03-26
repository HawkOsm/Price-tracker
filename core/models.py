from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base

class ProductModel(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    url = Column(String)
    selector = Column(String, nullable=True)
    added_date = Column(DateTime, default=datetime.utcnow)

    price_history = relationship("PriceHistoryModel", back_populates="product", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Product(name='{self.name}', url='{self.url}')>"

class PriceHistoryModel(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    price = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

    product = relationship("ProductModel", back_populates="price_history")

    def __repr__(self):
        return f"<PriceHistory(product_id={self.product_id}, price={self.price}, timestamp={self.timestamp})>"
