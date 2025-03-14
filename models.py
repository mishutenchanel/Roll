from sqlalchemy import Column, Integer, Float, Date
from database import Base

class Roll(Base):
    __tablename__ = "rolls"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    length = Column(Float, nullable=False)
    weight = Column(Float, nullable=False)
    date_added = Column(Date, nullable=False)
    date_removed = Column(Date, nullable=True)
