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
from typing import List

from app import db

from dateutil.relativedelta import relativedelta

from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import PropComparator
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import with_loader_criteria


class Base(DeclarativeBase):
    """Base declarative class"""

    pass


"""Incident to Component relation"""
IncidentComponentRelation = Table(
    "incident_component_relation",
    Base.metadata,
    Column("incident_id", ForeignKey("incident.id"), primary_key=True),
    Column("component_id", ForeignKey("component.id"), primary_key=True),
    Index("inc_comp_rel", "incident_id", "component_id", unique=True),
)


class Component(Base):
    """Component model"""

    __tablename__ = "component"

    id = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String())
    attributes: Mapped[List["ComponentAttribute"]] = relationship(
        back_populates="component"
    )

    incidents: Mapped[List["Incident"]] = relationship(
        secondary=IncidentComponentRelation, back_populates="components"
    )

    def __repr__(self):
        return "<Component {}: {}>".format(self.id, self.name)

    def as_string(self, attr_key):
        return "<Component {}: {} ({})>".format(
            self.id,
            self.name,
            self.get_attributes_as_dict()[attr_key]
        )

    @staticmethod
    def all():
        """Query all components with attributes"""
        return (
            db.session.scalars(
                select(Component)
                .options(joinedload(Component.attributes))
                .order_by(Component.name)
            )
            .unique()
            .all()
        )

    @staticmethod
    def all_with_active_incidents():
        """Query all components joined with active incidents for the component

        :returns: Components with attributes and incidents populated
        """
        return (
            db.session.scalars(
                select(Component)
                .options(joinedload(Component.attributes, innerjoin=True))
                .options(
                    joinedload(Component.incidents, innerjoin=False),
                    with_loader_criteria(
                        Incident,
                        PropComparator.and_(
                            Incident.end_date.is_(None),
                            Incident.start_date <= datetime.datetime.now(),
                        ),
                    ),
                )
                .order_by(Component.name)
            )
            .unique()
            .all()
        )

    def get_attributes_as_dict(self):
        """Return component attributes as dicionary"""
        return {attr.name: attr.value for attr in self.attributes}

    @staticmethod
    def count_components_by_attributes(attr_dict):
        """Return the number of components that match specific attributes"""
        counter = 0
        for comp in Component.all():
            comp_attrs = comp.get_attributes_as_dict()
            if set(
                comp_attrs.items()
            ).intersection(set(
                    attr_dict.items())) == set(attr_dict.items()):
                counter += 1
        return counter

    @staticmethod
    def find_by_name_and_attributes(name, attributes):
        """Find existing component by name and set of attributes

        Perform lookup and search for all components matching target name. For
        the results compare their attributes. When there is a full match -
        return it. Otherwise compare whether target attributes build a subset
        of existing component.

        :param str name: Component name.
        :param dict attributes: Attributes as dictionary

        :returns: `Component` entity when found, None otherwise
        """
        comps_by_name = db.session.scalars(
            select(Component).where(Component.name == name)
        ).all()
        for comp in comps_by_name:
            comp_attrs = comp.get_attributes_as_dict()
            if comp_attrs == attributes:
                # Shortcut - just return
                return comp
            if all(
                comp_attrs.get(key, None) == val
                for key, val in attributes.items()
            ):
                # Target attributes build a subset of current attributes -
                # a pretty good candidate when not much attributes were passed
                return comp
        return None

    def calculate_sla(self):
        """Calculate component availability on the month basis"""

        time_now = datetime.datetime.now()
        this_month_start = datetime.datetime(time_now.year, time_now.month, 1)

        outages = [inc for inc in self.incidents
                   if inc.impact == 3 and inc.end_date is not None]
        outages_dict = Incident.get_history_by_months(outages)
        outages_dict_sorted = dict(sorted(outages_dict.items()))

        prev_month_minutes = 0

        months = [this_month_start + relativedelta(months=-mon)
                  for mon in range(6)]
        sla_dict = {month: 1 for month in months}

        for month_start, outage_group in outages_dict_sorted.items():
            minutes_in_month = prev_month_minutes
            outages_minutes = 0
            prev_month_minutes = 0

            if this_month_start.month == month_start.month:
                minutes_in_month = (
                    time_now - month_start
                ).total_seconds() / 60
            else:
                next_month_start = month_start + relativedelta(months=1)
                minutes_in_month = (
                    next_month_start - month_start
                ).total_seconds() / 60

            for outage in outage_group:
                outage_start = outage.start_date
                if outage_start < month_start:
                    diff = month_start - outage_start
                    prev_month_minutes += diff.total_seconds() / 60
                    outage_start = month_start

                diff = outage.end_date - outage_start
                outages_minutes += diff.total_seconds() / 60

            sla_dict[month_start] = (
                minutes_in_month - outages_minutes
            ) / minutes_in_month

        return sla_dict

    @staticmethod
    def get_by_id(component_id):
        return db.session.scalars(
            select(Component).where(Component.id == component_id)
        ).first()


class ComponentAttribute(Base):
    """Component Attribute model"""

    __tablename__ = "component_attribute"
    id = mapped_column(Integer, primary_key=True, index=True)
    component_id = mapped_column(ForeignKey("component.id"), index=True)
    name: Mapped[str] = mapped_column(String(30))
    value: Mapped[str] = mapped_column(String(50))
    component: Mapped[Component] = relationship(back_populates="attributes")

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


class Incident(Base):
    """Incident model"""

    __tablename__ = "incident"
    id = mapped_column(Integer, primary_key=True, index=True)
    text: Mapped[str] = mapped_column(String())
    start_date: Mapped[datetime.datetime] = mapped_column(
        insert_default=func.now()
    )
    end_date: Mapped[datetime.datetime] = mapped_column(nullable=True)
    impact: Mapped[int] = mapped_column(db.SmallInteger)
    # upgrade: system: Mapped[bool] = mapped_column(Boolean, default=False)
    system: Mapped[bool] = mapped_column(Boolean, default=False)

    components: Mapped[List["Component"]] = relationship(
        back_populates="incidents", secondary=IncidentComponentRelation
    )

    updates: Mapped[List["IncidentStatus"]] = relationship(
        back_populates="incident",
        order_by="desc(IncidentStatus.timestamp)",
    )

    def __repr__(self):
        return "<Incident {}: {}>".format(self.id, self.text)

    @staticmethod
    def get_all_active():
        """Return active incidents and maintenances"""
        return db.session.scalars(
            select(Incident).filter(
                Incident.end_date.is_(None),
                Incident.start_date <= datetime.datetime.now(),
            )
        ).all()

    @staticmethod
    def get_all_closed():
        """Return closed incidents and maintenances"""
        return db.session.scalars(
            select(Incident).filter(
                Incident.end_date.is_not(None),
            )
        ).all()

    @staticmethod
    def get_history_by_months(incident_list):
        if incident_list is None:
            incident_list = Incident.get_all_closed()
        incident_dict = {}
        for incident in incident_list:
            incident_dict.setdefault(
                datetime.datetime(
                    incident.end_date.year,
                    incident.end_date.month,
                    1),
                []
            ).append(incident)
        return incident_dict

    @staticmethod
    def get_active_maintenance():
        """Return active maintenances

        :returns: `Incident`
        """
        return db.session.scalars(
            select(Incident).filter(
                # already started
                Incident.start_date <= datetime.datetime.now(),
                # not closed
                Incident.end_date.is_(None),
                Incident.impact == 0,
            )
        ).first()

    @staticmethod
    def get_active_m():
        """Return active manually opened incidents
        :returns: `Incident`s created by USER
        """
        return db.session.scalars(
            select(Incident).filter(
                # already started
                Incident.start_date <= datetime.datetime.now(),
                # not closed
                Incident.end_date.is_(None),
                Incident.impact != 0,
                Incident.system.is_(False),
            )
        ).all()

    @staticmethod
    def get_active():
        """Return active incident
        :returns: `Incident`s created by API
        """
        return db.session.scalars(
            select(Incident).filter(
                # already started
                Incident.start_date <= datetime.datetime.now(),
                # not closed
                Incident.end_date.is_(None),
                Incident.impact != 0,
                Incident.system.is_(True),
            )
        ).all()

    @staticmethod
    def get_by_id(incident_id):
        return db.session.scalars(
            select(Incident).where(Incident.id == incident_id)
        ).first()

    def get_attributes_by_key(self, attr_key):
        """Get Incident component attribute by key"""
        return set(
            c.get_attributes_as_dict().get(attr_key, None)
            for c in self.components
        )

    @staticmethod
    def get_view_by_component_attribute(attr_name, attr_value):
        """Get Incidents view by component attribute"""
        return db.session.scalars(
            select(Incident)
            .options(joinedload(Incident.updates, innerjoin=False))
            .options(
                joinedload(Incident.components, innerjoin=True).joinedload(
                    Component.attributes, innerjoin=True
                ),
                with_loader_criteria(
                    ComponentAttribute,
                    PropComparator.and_(
                        ComponentAttribute.name == attr_name,
                        ComponentAttribute.value == attr_value,
                    ),
                ),
            )
            .order_by(Incident.start_date.asc())
        ).unique()


class IncidentStatus(Base):
    """Incident Updates"""

    __tablename__ = "incident_status"
    id = mapped_column(Integer, primary_key=True, index=True)
    incident_id = mapped_column(ForeignKey("incident.id"), index=True)
    incident: Mapped["Incident"] = relationship(back_populates="updates")
    timestamp: Mapped[datetime.datetime] = mapped_column(
        db.DateTime, insert_default=func.now()
    )
    text: Mapped[str] = mapped_column(String())
    status: Mapped[str] = mapped_column(String())
