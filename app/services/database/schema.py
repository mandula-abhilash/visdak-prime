from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text

# Define the database schema
metadata = MetaData()

tasks = Table(
    'tasks',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('title', Text),
    Column('description', Text),
    Column('priority', String, nullable=False),
    Column('category', Text)
)