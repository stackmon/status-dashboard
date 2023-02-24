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

import datetime
import enum

from app import db

from sqlalchemy import Enum
from sqlalchemy import and_
from sqlalchemy import select


class IncidentComponentRelation(db.Model):
    """Incident to Component relation"""
    __tablename__ = "incident_component_relation"
    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey("incident.id"))
    component_id = db.Column(db.Integer, db.ForeignKey("component.id"))
    db.Index("inc_comp_rel", incident_id, component_id)


class Component(db.Model):
    """Component model"""
    id = db.Column(db.Integer, primary_key=True, index=True)
    name = db.Column(db.String)
    attributes = db.relationship("ComponentAttribute", backref="Component")
    incidents = db.relationship(
        "Incident",
        secondary=IncidentComponentRelation.__table__,
        backref="Component",
        lazy="dynamic",
    )

    def __repr__(self):
        return "<Component {}:{}>".format(self.id, self.name)

    def get_attributes_as_dict(self):
        """Return component attributes as dicionary"""
        return {attr.name: attr.value for attr in self.attributes}

    def get_open_incidents(self):
        """Return open incidents"""
        return self.incidents.filter(Incident.end_date.is_(None))


class ComponentAttribute(db.Model):
    """Component Attribute model"""

    __tablename__ = "component_attribute"
    __table_args__ = (db.UniqueConstraint(
        "component_id",
        "name",
        name="u_attr_comp"),)
    id = db.Column(db.Integer, primary_key=True, index=True)
    component_id = db.Column(
        db.Integer,
        db.ForeignKey("component.id"),
        index=True)
    name = db.Column(db.String)
    value = db.Column(db.String)

    def __repr__(self):
        return "<ComponentAttribute {}={}>".format(self.name, self.value)

    @staticmethod
    def get_unique_values(attr):
        """Return unique value by attribute name

        :param str attr: Attribute name to be used for filter

        :returns: List of unique `ComponentAttribute.value`s
        """
        return [r[0] for r in db.session.execute(
            select(ComponentAttribute.value)
            .filter(ComponentAttribute.name.is_(attr))
        ).unique().all()]


class IncidentImpactEnum(enum.Enum):
    maintenance = "maintenance"
    minor = "minor"
    major = "major"
    outage = "outage"


class Incident(db.Model):
    __tablename__ = "incident"
    id = db.Column(db.Integer, primary_key=True, index=True)
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
    id = db.Column(db.Integer, primary_key=True, index=True)
    incident_id = db.Column(
        db.Integer,
        db.ForeignKey("incident.id"),
        index=True)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now())
    text = db.Column(db.String)
    status = db.Column(db.String)
