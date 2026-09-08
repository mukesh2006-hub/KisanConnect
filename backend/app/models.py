from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime

from .database import Base

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    farmer_name = Column(String, nullable=False)
    crop = Column(String, default="Tomato")
    quantity = Column(Float, nullable=False)
    price_per_kg = Column(Float, nullable=False)
    quality = Column(String, default="Grade A")
    location = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    status = Column(String, default="AVAILABLE")
    created_at = Column(DateTime, default=datetime.utcnow)

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, nullable=False)
    buyer_name = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    delivery_lat = Column(Float, nullable=False)
    delivery_lon = Column(Float, nullable=False)
    status = Column(String, default="PLACED")
    created_at = Column(DateTime, default=datetime.utcnow)
