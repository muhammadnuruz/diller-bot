import uuid

from db.utils import CreateModel
from sqlalchemy import Integer, String, ForeignKey, Column, Numeric, JSON


class TelegramUser(CreateModel):
    __tablename__ = "telegramuser"
    chat_id = Column(String(50), nullable=False, unique=True)
    full_name = Column(String(255), nullable=True)
    username = Column(String(255), nullable=True)
    url = Column(String(500), nullable=True)
    login = Column(String(255), nullable=True)
    password = Column(String(255), nullable=True)
    price_type = Column(String(50), nullable=True)


class Card(CreateModel):
    __tablename__ = "card"
    name = Column(String(255), nullable=True)
    image = Column(String(255), nullable=True)
    price = Column(Numeric(20, 2), nullable=True)
    unique_link = Column(String(15), nullable=False, default=lambda: str(uuid.uuid4())[:15])
    user = Column(Integer, ForeignKey('telegramuser.id'))


class Basket(CreateModel):
    __tablename__ = "basket"
    shop = Column(Integer, ForeignKey("telegramuser.id"))
    card = Column(Integer, ForeignKey("card.id"))
    chat_id = Column(String(50), nullable=True)
    full_name = Column(String(255), nullable=True)
    username = Column(String(255), nullable=True)
    count = Column(Integer, default=0)


class Order(CreateModel):
    __tablename__ = 'order'
    shop = Column(Integer, ForeignKey("telegramuser.id"))
    chat_id = Column(String(50), nullable=True)
    full_name = Column(String(255), nullable=True)
    username = Column(String(255), nullable=True)
    cards = Column(JSON, nullable=True)
    total_sum = Column(Numeric(50, 2), nullable=True)
