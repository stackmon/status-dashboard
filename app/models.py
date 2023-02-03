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


class IncidentComponentRelation(db.Model):
    __tablename__ = "incident_component_relation"
    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey("incident.id"))
    component_id = db.Column(db.Integer, db.ForeignKey("component.id"))


class Component(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    type = db.Column(db.String)
    attributes = db.relationship("ComponentAttribute", backref="Component")

    def __repr__(self):
        return "<Component {}:{}>".format(self.id, self.name)

    def get_open_incidents_in_region(self, region_name):
        return Incident.get_open_for_component(self.id, region_name)

    def get_status(self, region_name):
        incidents = self.get_open_incidents_in_region(region_name)
        if len(incidents) == 0:
            status = "available"
        else:
            status = incidents[0].impact.value
        return status

    @staticmethod
    def component_by_region(component_id, region_name):
        component_by_region = (
            db.session.query(Component.id)
            .join(
                ComponentAttribute,
                ComponentAttribute.component_id == Component.id,
            )
            .filter(
                Component.id == component_id,
                ComponentAttribute.name == "region",
                ComponentAttribute.value == region_name,
            )
            .all()
        )
        return component_by_region[0] if len(component_by_region) > 0 else None

    @staticmethod
    def get_component_with_incident(component_id, region_name):
        component_with_incident = (
            db.session.query(Component.id, Incident.id, Incident.impact)
            .join(
                IncidentComponentRelation,
                and_(
                    Component.id == IncidentComponentRelation.component_id,
                    IncidentComponentRelation.component_id == component_id,
                ),
            )
            .join(
                Incident, IncidentComponentRelation.incident_id == Incident.id
            )
            .filter(
                Incident.end_date.is_(None), Incident.regions == region_name
            )
            .all()
        )
        return (
            component_with_incident[0]
            if len(component_with_incident) > 0
            else None
        )

    @staticmethod
    def component_by_category(component_id, category_name):
        component_by_category = (
            db.session.query(Component.id, Component.name)
            .join(
                ComponentAttribute,
                ComponentAttribute.component_id == Component.id,
            )
            .filter(
                Component.id == component_id,
                ComponentAttribute.name == "category",
                ComponentAttribute.value == category_name,
            )
            .all()
        )
        return (
            component_by_category[0]
            if len(component_by_category) > 0
            else None
        )

    @staticmethod
    def components_by_category(category_name):
        component_id_list = ()
        components_by_category = (
            db.session.query(Component.id)
            .join(
                ComponentAttribute,
                ComponentAttribute.component_id == Component.id,
            )
            .filter(
                ComponentAttribute.name == "category",
                ComponentAttribute.value == category_name,
            )
            .all()
        )
        if len(components_by_category) > 0:
            for component in components_by_category:
                component_id_list = component_id_list + (component.id,)
        return component_id_list if len(components_by_category) > 0 else None


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
    __tablename__ = "incident"
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
    def get_open_for_component(component_id, region_name):
        open_incident_for_component = (
            db.session.query(Incident)
            .join(
                IncidentComponentRelation,
                and_(
                    Incident.id == IncidentComponentRelation.incident_id,
                    IncidentComponentRelation.component_id == component_id,
                ),
            )
            .join(
                Component,
                IncidentComponentRelation.component_id == Component.id,
            )
            .filter(
                Incident.end_date.is_(None), Incident.regions == region_name
            )
            .all()
        )
        return open_incident_for_component


class IncidentStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey("incident.id"))
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now())
    text = db.Column(db.String)
    status = db.Column(db.String)
