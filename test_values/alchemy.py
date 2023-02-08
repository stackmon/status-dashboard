from sqlalchemy import (
    text,
    create_engine,
    MetaData,
    Table,
    Column,
)
from sqlalchemy.orm import create_session
from sqlalchemy.ext.declarative import declarative_base

db_uri = "sqlite:///example.sqlite"
comp_name = 'Application Operations Management'

engine = create_engine(db_uri, echo=True)
stmt_region = text("SELECT DISTINCT value FROM component_attribute WHERE name='region'")

Base = declarative_base()
metadata = MetaData(bind=engine)

class Component(Base):
    __table__ = Table("component", metadata, autoload=True)

class ComponentAttribute(Base):
    __table__ = Table("component_attribute", metadata, autoload=True)

session = create_session(bind=engine)

results = engine.execute(stmt_region).fetchone()[0]

print("QUERY OUTPUT")
#query = session.query(ComponentAttribute.value).join(
#    Component, ComponentAttribute.component_id == Component.id
#).filter(ComponentAttribute.name == "region").all()

query2 = session.query(Component.name).join(
    ComponentAttribute, ComponentAttribute.component_id == Component.id
).filter(Component.id == "2", ComponentAttribute.name == "region", ComponentAttribute.value == "EU-DE").all()

print(query2[0])


