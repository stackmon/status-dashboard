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

from app import db
from app.models import Component
from app.models import ComponentAttribute
from app.models import Incident
from app.models import IncidentImpactEnum
from app.models import IncidentStatus
from app.models import IncidentComponentRelation


def register(app):
    @app.cli.group()
    def bootstrap():
        """Bootstrap data"""
        pass

    @bootstrap.command()
    def purge():
        """Purge current configuration"""
        db.session.query(Component).delete()
        db.session.query(ComponentAttribute).delete()
        db.session.query(Incident).delete()
        db.session.query(IncidentStatus).delete()
        db.session.query(IncidentComponentRelation).delete()
        db.session.commit()

    @bootstrap.command()
    def provision():
        """Fill database with initial data"""
        import otc_metadata.services

        data = otc_metadata.services.Services()
        components = {}
        for region in ["EU-DE", "EU-NL", "Swiss"]:
            for cat in data.service_categories:
                for srv in data.services_by_category(cat["name"]):
                    #
                    # component attribute region
                    #
                    cat_attr = ComponentAttribute(
                        name="category", value=srv["service_category"]
                    )
                    db.session.add(cat_attr)
                    #
                    # component attribute category
                    #
                    reg_attr = ComponentAttribute(
                        name="region", value=region
                    )
                    db.session.add(reg_attr)

                    db_srv = Component(
                        name=srv["service_title"],
                        type=srv["service_type"],
                        attributes=[cat_attr, reg_attr],
                    )
                    db.session.add(db_srv)
                    # comp_id = (
                    #     db.session.query(Component.id)
                    #     .filter_by(name=srv["service_title"])
                    #     .first()[0]
                    components[srv["service_type"]] = db_srv
        inc1 = Incident(
            text="Test incident",
            impact=IncidentImpactEnum.outage,
            start_date=datetime.datetime.now(),
            regions="EU-DE",
            components=[components["ecs"], components["vpc"]],
        )
        db.session.add(inc1)
        inc2 = Incident(
            text="Test Maintenance",
            impact=IncidentImpactEnum.maintenance,
            start_date=datetime.datetime.now()
            - datetime.timedelta(minutes=30),
        )
        db.session.add(inc2)
        inc3 = Incident(
            text="Test Maintenance 2",
            impact=IncidentImpactEnum.maintenance,
            start_date=datetime.datetime.now()
            - datetime.timedelta(minutes=30),
            regions="Swiss",
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
