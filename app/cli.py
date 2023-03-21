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
from app.models import IncidentComponentRelation
from app.models import IncidentImpactEnum
from app.models import IncidentStatus


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

        components = {}
        for region in ["Region1", "Region2"]:
            components[region] = dict()
            for cat in range(1, 10):
                for srv in range(1, 10):
                    cat_attr = ComponentAttribute(
                        name="category",
                        value=f"Group{cat}"
                    )
                    db.session.add(cat_attr)
                    #
                    # component attribute category
                    #
                    reg_attr = ComponentAttribute(name="region", value=region)
                    db.session.add(reg_attr)

                    # Service type attribute
                    type_attr = ComponentAttribute(
                        name="type",
                        value=f"type{cat}-{srv}"
                    )
                    db.session.add(type_attr)

                    db_srv = Component(
                        name=f"Component {srv}",
                        attributes=[
                            cat_attr,
                            reg_attr],
                    )
                    db.session.add(db_srv)
                    components[region][f"type{cat}-{srv}"] = db_srv
        inc1 = Incident(
            text="Test incident",
            impact=IncidentImpactEnum.outage,
            start_date=datetime.datetime.now(),
            components=[
                components["Region1"]["type1-2"],
                components["Region1"]["type2-3"],
            ],
        )
        db.session.add(inc1)
        inc2 = Incident(
            text="Test Maintenance",
            impact=IncidentImpactEnum.maintenance,
            start_date=datetime.datetime.now()
            - datetime.timedelta(minutes=30),
            components=[
                components["Region1"]["type3-4"],
            ],
        )
        db.session.add(inc2)
        inc3 = Incident(
            text="Test Maintenance 2",
            impact=IncidentImpactEnum.maintenance,
            start_date=datetime.datetime.now()
            - datetime.timedelta(minutes=30),
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
