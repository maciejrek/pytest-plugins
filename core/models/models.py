from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base


class Car(Base):
    __tablename__ = 'car'

    id = Column(Integer, primary_key=True, autoincrement=True)
    rate = relationship('Rate', cascade='all, delete', uselist=False, back_populates='car')
    make = Column(String(length=50))
    model = Column(String(length=50))
    avg_rating = Column(Float, default=0.0)


class Rate(Base):
    __tablename__ = 'rate'
    id = Column(Integer, primary_key=True, autoincrement=True)
    car_id = Column(Integer, ForeignKey('car.id', ondelete="CASCADE"), nullable=False)
    car = relationship('Car', back_populates='rate')
    rating = Column(Integer)
