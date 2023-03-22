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

from app import db
from app.models import Component
from app.models import ComponentAttribute
from app.models import Incident
from app.models import IncidentComponentRelation
from app.models import IncidentStatus


def register(app):
    @app.cli.group()
    def bootstrap():
        """Bootstrap data"""
        pass

    @bootstrap.command()
    def purge():
        """Purge current configuration"""
        db.session.query(ComponentAttribute).delete()
        db.session.query(IncidentComponentRelation).delete()
        db.session.query(Component).delete()
        db.session.query(IncidentStatus).delete()
        db.session.query(Incident).delete()
        db.session.commit()

    @bootstrap.command()
    def provision():
        """Fill database with initial data"""

        if "CATALOG" not in app.config:
            return

        for target_component in app.config["CATALOG"]['components']:
            target_attrs = target_component.get("attributes", {})
            if not Component.find_by_name_and_attributes(
                target_component["name"], target_attrs
            ):
                db_attrs = []
                for (k, v) in target_attrs.items():
                    db_attr = ComponentAttribute(name=k, value=v)
                    db.session.add(db_attr)
                    db_attrs.append(db_attr)
                db_comp = Component(
                    name=target_component["name"],
                    attributes=db_attrs,
                )
                db.session.add(db_comp)

        db.session.commit()
