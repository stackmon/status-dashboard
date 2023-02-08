# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#

import enum
import datetime

from sqlalchemy import Enum
from sqlalchemy import and_


from app import db


# class ComponentRegionRelation(db.Model):
#     __tablename__ = "component_region_relation"
#     id = db.Column(db.Integer, primary_key=True)
#     region_id = db.Column(db.Integer, db.ForeignKey("region.id"))
#     component_id = db.Column(db.Integer, db.ForeignKey("component.id"))





# class IncidentRegionRelation(db.Model):
#     __tablename__ = "incident_region_relation"
#     id = db.Column(db.Integer, primary_key=True)
#     incident_id = db.Column(db.Integer, db.ForeignKey("incident.id"))
#     region_id = db.Column(db.Integer, db.ForeignKey("region.id"))


# class Region(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String)
#     components = db.relationship(
#         "Component",
#         secondary=ComponentRegionRelation.__table__,
#         backref="Region",
#         lazy="dynamic",
#     )
# 
#     def __repr__(self):
#         return "<Region {}>".format(self.name)
# 
#     def components_by_category(self, category):
#         return self.components.filter(Component.category_id == category)


# class ComponentCategory(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String)
#     components = db.relationship("Component", backref="category")
# 
#     def __repr__(self):
#         return "<ComponentCategory {}>".format(self.name)

class IncidentComponentRelation(db.Model):
    __tablename__ = "incident_component_relation"
    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey("incident.id"))
    component_id = db.Column(db.Integer, db.ForeignKey("component.id"))

class Component(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    type = db.Column(db.String)
    # category_id = db.Column(db.Integer, db.ForeignKey("component_category.id"))
    attributes = db.relationship(
        "ComponentAttribute",
        backref="Component"
        )

    def __repr__(self):
        return "<Component {}:{}:{}>".format(
            self.id, self.category.name, self.name
        )

    def get_status(self, region_id):
        incidents = self.get_open_incidents_in_region(region_id)
        if len(incidents) == 0:
            return "available"
        else:
            return incidents[0].impact.value

    @staticmethod
    def component_by_region(comp_name, region_name):
        return (
            db.session.query(Component.name)
            .join(
                ComponentAttribute, ComponentAttribute.component_id == Component.id
                )
                .filter(
                    Component.name == comp_name,
                    ComponentAttribute.name == "region",
                    ComponentAttribute.value == region_name
                    )
                .all()
        )

    def get_open_incidents_in_region(self, region_id):
        return Incident.get_open_for_component(self.id, region_id)

class ComponentAttribute(db.Model):
    __tablename__ = "component_attribute"
    id = db.Column(db.Integer, primary_key=True)
    component_id = db.Column(db.Integer, db.ForeignKey("component.id"))
    name = db.Column(db.String)
    value = db.Column(db.String)
    
    def __repr__(self):
        return "<ComponentAttribute {}>".format(self.name)


class IncidentImpactEnum(enum.Enum):
    maintenance = "maintenance"
    minor = "minor"
    major = "major"
    outage = "outage"

class Incident(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    impact = db.Column(Enum(IncidentImpactEnum))
    components = db.relationship(
        "Component",
        secondary=IncidentComponentRelation.__table__,
        backref="Incident",
        lazy="dynamic",
    )
    regions = db.Column(db.String)
    updates = db.relationship(
        "IncidentStatus",
        backref="incident",
        order_by="desc(IncidentStatus.timestamp)",
    )

    def __repr__(self):
        return "<Incident {}>".format(self.text)

    @staticmethod
    def open():
        return Incident.query.filter(Incident.end_date.is_(None)).all()

    @staticmethod
    def closed():
        return Incident.query.filter(Incident.end_date.is_not(None)).all()

    @staticmethod
    def get_open_for_component(component_id, region_id):
        """List open incidents affecting component in region"""
        return (
            db.session.query(Incident)
            .join(
                IncidentComponentRelation,
                and_(
                    Incident.id == IncidentComponentRelation.incident_id,
                    IncidentComponentRelation.component_id == component_id,
                ),
            )
            # .join(
            #     IncidentRegionRelation,
            #     and_(
            #         Incident.id == IncidentRegionRelation.incident_id,
            #         IncidentRegionRelation.region_id == region_id,
            #     ),
            # )
            .filter(Incident.end_date.is_(None))
            .all()
        )


class IncidentStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey("incident.id"))
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now())
    text = db.Column(db.String)
    status = db.Column(db.String)
