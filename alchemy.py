import os
from sqlalchemy import *
from sqlalchemy.orm import create_session
from sqlalchemy.orm import load_only
from sqlalchemy import select
from sqlalchemy.ext.declarative import declarative_base
 

db_uri = "sqlite:///example.sqlite"
 
Base = declarative_base()
engine = create_engine(db_uri, echo=True)
metadata = MetaData(bind=engine)
 
class ComponentAttribute(Base):
    __table__ = Table('component_attribute', metadata, autoload=True)

def show_query_result(res):
    for attr in res:
        print(attr.name + attr.value)
 
 # Создать транзакцию
session = create_session(bind=engine)
 
 # Проверить функцию запроса к базе данных
res = session.query(ComponentAttribute).with_entities(ComponentAttribute.value,ComponentAttribute.name).all()

show_query_result(res)
 
print('-' * 15)
