from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import Column, DateTime, func, Integer, select, update, and_, delete
from sqlalchemy.exc import SQLAlchemyError

from db import db, Base


class AbstractClass:
    @staticmethod
    async def commit():
        try:
            await db.commit()
        except Exception:
            await db.rollback()
            raise

    @classmethod
    async def create_or_update(cls, chat_id, **kwargs):
        async with await db.get_session() as session:
            result = await session.execute(
                select(cls).where(cls.chat_id == chat_id)
            )
            instance = result.scalar_one_or_none()

            if instance:
                await session.execute(
                    update(cls)
                    .where(cls.chat_id == chat_id)
                    .values(**kwargs)
                    .execution_options(synchronize_session="fetch")
                )
                await session.refresh(instance)
            else:
                instance = cls(chat_id=chat_id, **kwargs)
                session.add(instance)

            await session.commit()
            return instance

    @classmethod
    async def create_or_update_basket(cls, card, chat_id, count: int, **kwargs):
        async with await db.get_session() as session:
            result = await session.execute(
                select(cls).where(
                    and_(
                        cls.chat_id == chat_id,
                        cls.card == card
                    )
                )
            )
            instance = result.scalar_one_or_none()

            if instance:
                instance.count += count
                for key, value in kwargs.items():
                    setattr(instance, key, value)
            else:
                instance = cls(chat_id=chat_id, card=card, count=count, **kwargs)
                session.add(instance)

            await session.commit()
            return instance

    @classmethod
    async def get_by(cls, **filters):
        async with await db.get_session() as session:
            stmt = select(cls).filter_by(**filters)
            result = await session.execute(stmt)
            return result.scalars().all()

    @classmethod
    async def create(cls, **kwargs):
        async with await db.get_session() as session:
            obj = cls(**kwargs)
            session.add(obj)
            await session.commit()
            return obj

    @classmethod
    async def get_total_price(cls, shop_id: int, user_id: str, CardModel):
        async with await db.get_session() as session:
            query = select(cls.count, CardModel.price).join(CardModel).where(
                and_(
                    cls.chat_id == user_id,
                    CardModel.user == shop_id
                )
            )
            result = await session.execute(query)
            baskets = result.all()

            total_price = sum(count * price for count, price in baskets)
            return total_price

    @classmethod
    async def delete(cls, chat_id):
        async with await db.get_session() as session:
            query = delete(cls).where(chat_id == chat_id)
            await session.execute(query)
            await session.commit()

    @classmethod
    async def create_order(cls, user_id: str, shop_id: int, BasketModel, OrderModel, CardModel, full_name, username):
        async with await db.get_session() as session:
            try:
                query = select(
                    BasketModel.id,
                    BasketModel.card,
                    BasketModel.count,
                    CardModel.name,
                    CardModel.price
                ).join(
                    CardModel,
                    BasketModel.card == CardModel.id
                ).where(
                    and_(
                        BasketModel.chat_id == user_id,
                        CardModel.user == shop_id
                    )
                )

                result = await session.execute(query)
                baskets = result.all()

                if not baskets:
                    return None

                cards_data = []
                total_sum = Decimal('0')
                basket_ids = []

                for basket_id, card_id, count, name, price in baskets:
                    if count <= 0:
                        continue

                    if price is None or price < 0:
                        continue

                    item_total = Decimal(str(price)) * count
                    cards_data.append({
                        "card_id": card_id,
                        "name": name,
                        "count": count,
                        "price": float(price),
                        "item_total": float(item_total)
                    })

                    total_sum += item_total
                    basket_ids.append(basket_id)

                if not cards_data:
                    return None

                order = OrderModel(
                    chat_id=user_id,
                    full_name=full_name,
                    username=username,
                    shop=shop_id,
                    cards=cards_data,
                    total_sum=total_sum
                )

                session.add(order)

                await session.execute(
                    delete(BasketModel).where(BasketModel.id.in_(basket_ids))
                )

                await session.commit()
                await session.refresh(order)

                return order

            except SQLAlchemyError:
                await session.rollback()
                raise
            except Exception:
                await session.rollback()
                raise

    @classmethod
    async def check_and_update_purchases(cls):
        async with await db.get_session() as session:
            try:
                today = datetime.utcnow()

                stmt = (
                    update(cls)
                    .where(
                        cls.is_purchase.is_(True),
                        cls.purchase_data < today
                    )
                    .values(is_purchase=False)
                )

                await session.execute(stmt)
                await session.commit()

            except SQLAlchemyError:
                await session.rollback()
                raise
            except Exception:
                await session.rollback()
                raise


class CreateModel(Base, AbstractClass):
    __abstract__ = True
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
