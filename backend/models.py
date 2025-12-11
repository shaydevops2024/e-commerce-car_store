import os
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Numeric, Text, TIMESTAMP, ForeignKey
from sqlalchemy.sql import text
from dotenv import load_dotenv

load_dotenv()

PG_HOST = os.getenv('POSTGRES_HOST', 'localhost')
PG_PORT = os.getenv('POSTGRES_PORT', '5432')
PG_DB = os.getenv('POSTGRES_DB', 'carstore')
PG_USER = os.getenv('POSTGRES_USER', 'caruser')
PG_PASS = os.getenv('POSTGRES_PASSWORD', 'carpass')

DATABASE_URL = f"postgresql://{PG_USER}:{PG_PASS}@{PG_HOST}:{PG_PORT}/{PG_DB}"

engine = create_engine(DATABASE_URL, future=True)
metadata = MetaData()

cars = Table(
    'cars', metadata,
    Column('id', Integer, primary_key=True),
    Column('make', String(100)),
    Column('model', String(100)),
    Column('year', Integer),
    Column('price', Numeric(12,2)),
    Column('description', Text),
    Column('image', String(512)),
)

orders = Table(
    'orders', metadata,
    Column('id', Integer, primary_key=True),
    Column('created_at', TIMESTAMP),
    Column('status', String(50)),
    Column('total', Numeric(12,2)),
    Column('customer_name', String(200)),
    Column('customer_email', String(200)),
)

order_items = Table(
    'order_items', metadata,
    Column('id', Integer, primary_key=True),
    Column('order_id', Integer, ForeignKey('orders.id')),
    Column('car_id', Integer, ForeignKey('cars.id')),
    Column('quantity', Integer),
    Column('price', Numeric(12,2)),
)

def get_connection():
    return engine.connect()

