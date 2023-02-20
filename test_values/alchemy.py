from sqlalchemy import (
    text,
    create_engine,
    MetaData,
    Table,
    Column,
)
from sqlalchemy.orm import create_session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import and_

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

class Incident(Base):
    __table__ = Table("incident", metadata, autoload=True)

class IncidentComponentRelation(Base):
    __table__ = Table("incident_component_relation", metadata, autoload=True)

session = create_session(bind=engine)

results = engine.execute(stmt_region).fetchone()[0]

print("QUERY OUTPUT")
#query = session.query(ComponentAttribute.value).join(
#    Component, ComponentAttribute.component_id == Component.id
#).filter(ComponentAttribute.name == "region").all()

#query2 = session.query(Component.name).join(
#    ComponentAttribute, ComponentAttribute.component_id == Component.id
#).filter(Component.id == "2", ComponentAttribute.name == "region", ComponentAttribute.value == "EU-DE").all()

#print(query2[0])

component_id = 12
region = "EU-DE"
category_name = "application"

def get_component_with_inc(component_id, region):
    component_with_incident = session.query(Component.id, Incident.id, Incident.impact).join(
        IncidentComponentRelation,
        and_(
            Component.id == IncidentComponentRelation.component_id,
            IncidentComponentRelation.component_id == component_id,
        ),
    ).join(
        Incident, IncidentComponentRelation.incident_id == Incident.id
    ).filter(
        Incident.end_date.is_(None), Incident.regions == region
        ).all()
    print("COMPONENT NAME IS:")
    return component_with_incident[0]


def component_by_category(component_id, category_name):
    component_by_category = session.query(Component).join(
        ComponentAttribute, ComponentAttribute.component_id == Component.id
        ).filter(
            Component.id == component_id,
            ComponentAttribute.name == "category",
            ComponentAttribute.value == category_name,
        ).all()
    return component_by_category[0] if len(component_by_category) > 0 else None

def get_open_for_component(component_id, region_name):
    incident_for_component = session.query(Incident).join(
        IncidentComponentRelation,
        and_(
            Incident.id == IncidentComponentRelation.incident_id,
            IncidentComponentRelation.component_id == component_id,
        ),
        ).join(
            Component, IncidentComponentRelation.component_id == Component.id
        ).filter(
            Incident.end_date.is_(None), Incident.regions == region_name
        ).all()
    return  incident_for_component[0] if len(incident_for_component) > 0 else None


def component_by_region(component_id, region_name):
    component_by_region = session.query(Component.id).join(
        ComponentAttribute,
        ComponentAttribute.component_id == Component.id
        ).filter(
            Component.id == component_id,
            ComponentAttribute.name == "region",
            ComponentAttribute.value == region_name
        ).all()
    return component_by_region[0] if len(component_by_region) > 0 else None

print("#" * 20)
print("#" * 20)
print("#" * 20)

if __name__ == "__main__":
    #get_component_by_inc(13)
    #print("region is:" + region)
    #print(get_component_with_inc(12, region))
    #print("name is: ")
    #component_obj = component_by_category(1, category_name)
    #print("name is: ")
    #print(component_obj)
    #print(dir(components_by_category(category_name)[0]))

    #incident = get_open_for_component(12, "EU-DE")
    #print((incident).text)

    ogj = component_by_region(50, "EU-DE")
    print("name is: ")
    if ogj is not None:
        print(ogj[0])
    else:
        print(ogj)