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
from functools import wraps

from app import db

from flask import current_app
from flask import jsonify
from flask import make_response
from flask import session

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
    attributes = db.relationship(
        "ComponentAttribute",
        lazy="joined",  # makes sense to fetch immediately
    )
    incidents = db.relationship(
        "Incident",
        secondary=IncidentComponentRelation.__table__,
        lazy="select",  # fetch only on demand
    )

    def __repr__(self):
        return "<Component {}:{}>".format(self.id, self.name)

    def get_attributes_as_dict(self):
        """Return component attributes as dicionary"""
        return {attr.name: attr.value for attr in self.attributes}

    def get_open_incidents(self, incidents=None):
        """Return open incidents"""
        return Incident.get_open_for_component(self.id)

    @staticmethod
    def query_all_with_active_incidents():
        """Query all components joined with active incidents for the component

        :returns: tuple with 1st element - Component,
            2nd elemenet - Incident
        """
        return (
            db.session.query(Component, Incident)
            .join(
                IncidentComponentRelation,
                and_(
                    IncidentComponentRelation.component_id == Component.id,
                ),
                isouter=True,
            )
            .join(
                Incident,
                and_(
                    IncidentComponentRelation.incident_id == Incident.id,
                    Incident.start_date <= datetime.datetime.now(),
                    Incident.end_date.is_(None),
                ),
                isouter=True,
            )
        )


class ComponentAttribute(db.Model):
    """Component Attribute model"""

    __tablename__ = "component_attribute"
    __table_args__ = (
        db.UniqueConstraint("component_id", "name", name="u_attr_comp"),
    )
    id = db.Column(db.Integer, primary_key=True, index=True)
    component_id = db.Column(
        db.Integer, db.ForeignKey("component.id"), index=True
    )
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
        return [
            r[0]
            for r in db.session.execute(
                select(ComponentAttribute.value).where(
                    ComponentAttribute.name == attr
                )
            )
            .unique()
            .all()
        ]


class IncidentImpactEnum(enum.Enum):
    """Incident Impact Enum"""
    maintenance = "maintenance"
    minor = "minor"
    major = "major"
    outage = "outage"


class Incident(db.Model):
    """Incident model"""
    __tablename__ = "incident"
    id = db.Column(db.Integer, primary_key=True, index=True)
    text = db.Column(db.String)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    impact = db.Column(Enum(IncidentImpactEnum))
    components = db.relationship(
        "Component",
        secondary=IncidentComponentRelation.__table__,
        back_populates="incidents",
        lazy="dynamic",
    )
    updates = db.relationship(
        "IncidentStatus",
        backref="incident",
        lazy="dynamic",
        order_by="desc(IncidentStatus.timestamp)",
    )

    def __repr__(self):
        return "<Incident {}>".format(self.text)

    @staticmethod
    def open():
        return Incident.query.filter(Incident.end_date.is_(None))

    @staticmethod
    def closed():
        return Incident.query.filter(Incident.end_date.is_not(None))

    @staticmethod
    def get_open_for_component(component_id):
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
                Incident.end_date.is_(None),
            )
            .all()
        )
        return open_incident_for_component

    def get_attributes_by_key(self, attr_key):
        """Get Incident component attribute by key"""
        return {c.get_attributes_as_dict()[attr_key] for c in self.components}


class IncidentStatus(db.Model):
    """Incident Updates"""
    id = db.Column(db.Integer, primary_key=True, index=True)
    incident_id = db.Column(
        db.Integer, db.ForeignKey("incident.id"), index=True
    )
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now())
    text = db.Column(db.String)
    status = db.Column(db.String)


def auth_required(f):
    """Decorator to ensure authorized actions"""
    @wraps(f)
    def decorator(*args, **kwargs):
        # ensure the user object is in the session
        if 'user' not in session:
            return make_response(jsonify({"message": "Invalid token!"}), 401)
        current_user = session.get('user')
        required_group = current_app.config.get("OPENID_REQUIRED_GROUP")

        if required_group:
            if required_group not in current_user["groups"]:
                current_app.logger.info(
                    "Not logging in user %s due to lack of required groups"
                    % current_user.get(
                        "preferred_username",
                        current_user.get("name")
                    )
                )
                return make_response(
                    jsonify(
                        {"message": "Invalid User privileges!"}), 401)

        # Return the user information attached to the token
        return f(current_user, *args, **kwargs)
    return decorator
