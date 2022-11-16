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


class ServiceRegionRelation(db.Model):
    __tablename__ = "service_region_relation"
    id = db.Column(db.Integer, primary_key=True)
    region_id = db.Column(db.Integer, db.ForeignKey("region.id"))
    service_id = db.Column(db.Integer, db.ForeignKey("service.id"))


class IncidentServiceRelation(db.Model):
    __tablename__ = "incident_service_relation"
    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey("incident.id"))
    service_id = db.Column(db.Integer, db.ForeignKey("service.id"))


class IncidentRegionRelation(db.Model):
    __tablename = "incident_region_relation"
    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey("incident.id"))
    region_id = db.Column(db.Integer, db.ForeignKey("region.id"))


class Region(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    services = db.relationship(
        "Service",
        secondary=ServiceRegionRelation.__table__,
        backref="Region",
        lazy="dynamic",
    )

    def __repr__(self):
        return "<Region {}>".format(self.name)

    def services_by_category(self, category):
        return self.services.filter(Service.category_id == category)


class ServiceCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    services = db.relationship("Service", backref="category")

    def __repr__(self):
        return "<ServiceCategory {}>".format(self.name)


class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    type = db.Column(db.String)
    category_id = db.Column(db.Integer, db.ForeignKey("service_category.id"))

    def __repr__(self):
        return "<Service {}:{}:{}>".format(
            self.id, self.category.name, self.name
        )

    def get_status(self, region_id):
        incidents = self.get_open_incidents_in_region(region_id)
        if len(incidents) == 0:
            return "available"
        else:
            return incidents[0].impact.value

    def get_open_incidents_in_region(self, region_id):
        return Incident.get_open_for_service(self.id, region_id)


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
    services = db.relationship(
        "Service",
        secondary=IncidentServiceRelation.__table__,
        backref="Incident",
        lazy="dynamic",
    )
    regions = db.relationship(
        "Region",
        secondary=IncidentRegionRelation.__table__,
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
    def get_open_for_service(service_id, region_id):
        """List open incidents affecting service in region"""
        return (
            db.session.query(Incident)
            .join(
                IncidentServiceRelation,
                and_(
                    Incident.id == IncidentServiceRelation.incident_id,
                    IncidentServiceRelation.service_id == service_id,
                ),
            )
            .join(
                IncidentRegionRelation,
                and_(
                    Incident.id == IncidentRegionRelation.incident_id,
                    IncidentRegionRelation.region_id == region_id,
                ),
            )
            .filter(Incident.end_date.is_(None))
            .all()
        )


class IncidentStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    incident_id = db.Column(db.Integer, db.ForeignKey("incident.id"))
    timestamp = db.Column(db.DateTime, default=datetime.datetime.now())
    text = db.Column(db.String)
    status = db.Column(db.String)
