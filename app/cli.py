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

from app.models import Region
from app.models import Service
from app.models import ServiceCategory
from app.models import ServiceRegionRelation
from app.models import Incident
from app.models import IncidentImpactEnum
from app.models import IncidentStatus
from app.models import IncidentRegionRelation
from app.models import IncidentServiceRelation


def register(app):
    @app.cli.group()
    def bootstrap():
        """Bootstrap data"""
        pass

    @bootstrap.command()
    def purge():
        """Purge current configuration"""
        db.session.query(Region).delete()
        db.session.query(Service).delete()
        db.session.query(ServiceCategory).delete()
        db.session.query(Incident).delete()
        db.session.query(IncidentStatus).delete()
        db.session.query(IncidentServiceRelation).delete()
        db.session.query(IncidentRegionRelation).delete()
        db.session.query(ServiceRegionRelation).delete()
        db.session.commit()

    @bootstrap.command()
    def provision():
        """Fill database with initial data"""

        import otc_metadata.services
        data = otc_metadata.services.Services()

        r1 = Region(name="EU-DE")
        r2 = Region(name="EU-NL")
        r3 = Region(name="Swiss")
        services = {}
        for cat in data.service_categories:
            db_cat = ServiceCategory(name=cat["title"])
            db.session.add(db_cat)
            for srv in data.services_by_category(cat["name"]):
                db_srv = Service(
                    name=srv["service_title"],
                    type=srv["service_type"],
                    category=db_cat,
                )
                services[srv["service_type"]] = db_srv
                r1.services.append(db_srv)
                r2.services.append(db_srv)
                db.session.add(db_srv)

        db.session.add(r1)
        db.session.add(r2)
        db.session.add(r3)

        inc1 = Incident(
            text="Test incident",
            impact=IncidentImpactEnum.outage,
            start_date=datetime.datetime.now(),
            regions=[r1],
            services=[services["ecs"], services["vpc"]],
        )
        db.session.add(inc1)
        inc2 = Incident(
            text="Test Maintenance",
            impact=IncidentImpactEnum.maintenance,
            start_date=datetime.datetime.now()
            - datetime.timedelta(minutes=30),
            regions=[r1, r2, r3],
        )
        db.session.add(inc2)
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
                text="Fix is deployed. Service is recovering",
                status="fix_deployed",
            )
        )

        db.session.commit()
