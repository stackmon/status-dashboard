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

import otc_metadata.services

from app import db

# from app.models import Region
from app.models import Component
# from app.models import ComponentCategory
from app.models import ComponentAttribute
# from app.models import ComponentRegionRelation
from app.models import Incident
from app.models import IncidentImpactEnum
from app.models import IncidentStatus
# from app.models import IncidentRegionRelation
from app.models import IncidentComponentRelation


data = otc_metadata.services.Services()


def register(app):
    @app.cli.group()
    def bootstrap():
        """Bootstrap data"""
        pass

    @bootstrap.command()
    def purge():
        """Purge current configuration"""
        # db.session.query(Region).delete()
        db.session.query(Component).delete()
        # db.session.query(ComponentCategory).delete()
        db.session.query(ComponentAttribute).delete()
        db.session.query(Incident).delete()
        db.session.query(IncidentStatus).delete()
        db.session.query(IncidentComponentRelation).delete()
        # db.session.query(IncidentRegionRelation).delete()
        # db.session.query(ComponentRegionRelation).delete()
        db.session.commit()

    @bootstrap.command()
    def provision():
        """Fill database with initial data"""
        r1 = "EU-DE"
        r2 = "EU-NL"
        r3 = "Swiss"
        regions={r1: "EU-DE", r2: "EU-NL", r3: "Swiss"}
        components = {}
        for cat in data.service_categories:
            # db_cat = ComponentCategory(name=cat["title"])
            # db.session.add(db_cat)
            for srv in data.services_by_category(cat["name"]):
                cat_attr = ComponentAttribute(name="category", value=srv["service_category"])
                db.session.add(cat_attr)
                db_srv = Component(
                    name=srv["service_title"],
                    type=srv["service_type"],
                    attributes=[cat_attr],
                )
                db.session.add(db_srv)

                for region in ["EU-DE", "EU-NL", "Swiss"]:
                    comp_id = db.session.query(Component.id).filter_by(name=srv["service_title"]).first()[0]
                    reg_attr = ComponentAttribute(component_id=comp_id, name="region", value=region)
                    db.session.add(reg_attr)
                components[srv["service_type"]] = db_srv
                # r1.components.append(db_srv)
                # r2.components.append(db_srv)
                # db.session.add(db_srv)
        # db.session.add(a1)
        # db.session.add(r1)
        # db.session.add(r2)
        # db.session.add(r3)
        print("COMPONENTS:")
        print(components)
        print(components["ecs"])

        inc1 = Incident(
            text="Test incident",
            impact=IncidentImpactEnum.outage,
            start_date=datetime.datetime.now(),
            regions=regions[r1],
            components=[components["ecs"], components["vpc"]],
        )
        db.session.add(inc1)
        inc2 = Incident(
            text="Test Maintenance",
            impact=IncidentImpactEnum.maintenance,
            start_date=datetime.datetime.now()
            - datetime.timedelta(minutes=30),
            regions=regions[r2],
        )
        db.session.add(inc2)
        inc3 = Incident(
            text="Test Maintenance 2",
            impact=IncidentImpactEnum.maintenance,
            start_date=datetime.datetime.now()
            - datetime.timedelta(minutes=30),
            regions=regions[r3],
        )
        db.session.add(inc3)
        db.session.add(
            IncidentStatus(
                incident=inc2,
                timestamp=datetime.datetime.now()
                - datetime.timedelta(minutes=5),
                text="We have started working",
                status="started",
            )
        )
        db.session.add(
            IncidentStatus(
                incident=inc2,
                timestamp=datetime.datetime.now(),
                text="We have finished upgrade. Watching",
                status="watching",
            )
        )
        db.session.add(
            IncidentStatus(
                incident=inc3,
                timestamp=datetime.datetime.now()
                - datetime.timedelta(minutes=5),
                text="We have started working",
                status="started",
            )
        )
        db.session.add(
            IncidentStatus(
                incident=inc3,
                timestamp=datetime.datetime.now(),
                text="We have finished upgrade. Watching",
                status="watching",
            )
        )
        db.session.add(
            IncidentStatus(
                incident=inc1,
                timestamp=datetime.datetime.now()
                - datetime.timedelta(minutes=30),
                text="We are investigating issue reports",
                status="investigating",
            )
        )
        db.session.add(
            IncidentStatus(
                incident=inc1,
                timestamp=datetime.datetime.now()
                - datetime.timedelta(minutes=25),
                text="We have identified an issue and working on resolution",
                status="fixing",
            )
        )
        db.session.add(
            IncidentStatus(
                incident=inc1,
                timestamp=datetime.datetime.now()
                - datetime.timedelta(minutes=20),
                text="Fix is deployed. Component is recovering",
                status="fix_deployed",
            )
        )

        db.session.commit()
