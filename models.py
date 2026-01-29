from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, Numeric
from sqlalchemy.orm import relationship
from database import Base
from utils.current_time import get_current_time

class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    user_uuid = Column(String(36), unique=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=True)
    is_active = Column(Boolean, default=True)
    tracking = relationship("Tracking", back_populates='user')

class Products(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, index=True)
    amazon_url = Column(Text, nullable=False)
    current_price = Column(Numeric(10, 2))
    last_checked = Column(DateTime(timezone=True), default=get_current_time)
    title = Column(String(500))
    image_url = Column(String, nullable=True)
    tracking = relationship("Tracking", back_populates='product')
    history = relationship("PriceHistory", back_populates='product')

class PriceHistory(Base):
    __tablename__ = 'price_history'

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey('products.id'), index=True)
    price = Column(Numeric(10, 2), index=True)
    recorded_at = Column(DateTime(timezone=True), default=get_current_time)
    product = relationship('Products', back_populates='history')

class Tracking(Base):
    __tablename__ = 'tracking'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    created_at = Column(DateTime(timezone=True), default=get_current_time)
    initial_price = Column(Numeric(10, 2), index=True)
    last_alert_price = Column(Numeric(10, 2), default=None)
    user = relationship("Users", back_populates='tracking')
    product = relationship("Products", back_populates='tracking')
