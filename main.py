import json
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from sqlalchemy import create_engine, select, or_
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session

from models import Base, Publisher, Book, Shop, Stock, Sale


DB_USER = 'postgres'
DB_PASSWORD = 'Evyzirf777'
DB_HOST = 'localhost'
DB_PORT = 5432
DB_NAME = 'books_db'

DATABASE_URL = URL.create(
    drivername='postgresql+psycopg2',
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME
)


def create_tables(engine):
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def load_fixtures(session, file_path='fixtures.json'):
    model_map = {
        'publisher': Publisher,
        'book': Book,
        'shop': Shop,
        'stock': Stock,
        'sale': Sale,
    }

    path = Path(file_path)

    with path.open('r', encoding='utf-8') as f:
        data = json.load(f)

    for record in data:
        model_name = record['model']
        pk = record['pk']
        fields = record['fields']

        if model_name == 'sale':
            fields['price'] = Decimal(str(fields['price']))
            fields['date_sale'] = datetime.strptime(fields['date_sale'], '%Y-%m-%d').date()

        obj = model_map[model_name](id=pk, **fields)
        session.add(obj)

    session.commit()


def get_sales_by_publisher(session, publisher_input):
    conditions = [Publisher.name == publisher_input]

    if publisher_input.isdigit():
        conditions.append(Publisher.id == int(publisher_input))

    stmt = (
        select(Book.title, Shop.name, Sale.price, Sale.date_sale)
        .join(Stock, Sale.id_stock == Stock.id)
        .join(Book, Stock.id_book == Book.id)
        .join(Publisher, Book.id_publisher == Publisher.id)
        .join(Shop, Stock.id_shop == Shop.id)
        .where(or_(*conditions))
        .order_by(Sale.date_sale.desc())
    )

    return session.execute(stmt).all()


def main():
    try:
        engine = create_engine(DATABASE_URL, echo=False)

        create_tables(engine)

        with Session(engine) as session:
            load_fixtures(session, 'fixtures.json')

            publisher_input = input('Введите имя или id издателя: ').strip()
            sales = get_sales_by_publisher(session, publisher_input)

            if not sales:
                print('Ничего не найдено')
                return

            for title, shop_name, price, sale_date in sales:
                print(f'{title} | {shop_name} | {int(price)} | {sale_date.strftime("%d-%m-%Y")}')

    except Exception as e:
        print('Ошибка при работе с базой данных:')
        print(e)


if __name__ == '__main__':
    main()