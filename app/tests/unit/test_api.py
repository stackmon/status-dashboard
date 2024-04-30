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
import json
from unittest import TestCase


from app import create_app
from app import db
from app.models import Base
from app.models import Component
from app.models import ComponentAttribute
from app.models import Incident


import jwt


class TestBase(TestCase):

    test_config = dict(
        TESTING=True, SQLALCHEMY_DATABASE_URI="sqlite:///:memory:"
    )

    def setUp(self):
        self.app = create_app(self.test_config)
        with self.app.app_context():
            Base.metadata.create_all(bind=db.engine)
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            Base.metadata.drop_all(bind=db.engine)


class TestComponentStatus(TestBase):
    def setUp(self):
        super().setUp()

        self.client = self.app.test_client()
        # prepare jwt token
        payload = {"stackmon": "dummy"}
        encoded = jwt.encode(
            payload, self.app.config["SECRET_KEY"], algorithm="HS256"
        )

        self.headers = {"Authorization": f"bearer {encoded}"}

        with self.app.app_context():
            attr1 = ComponentAttribute(name="a1", value="v1")
            attr2 = ComponentAttribute(name="a2", value="v2")
            attr3 = ComponentAttribute(name="a1", value="v1")
            db.session.add(attr1)
            db.session.add(attr2)
            db.session.add(attr3)
            comp1 = Component(name="cmp1", attributes=[attr1, attr2])
            comp2 = Component(name="cmp2", attributes=[attr3])
            db.session.add(comp1)
            db.session.add(comp2)

            db.session.add(
                Incident(
                    text="inc",
                    components=[comp1],
                    impact=1,
                    end_date=datetime.datetime.now()
                    - datetime.timedelta(days=1),
                )
            )
            db.session.commit()

    def test_get_plain(self):
        res = self.client.get("/api/v1/component_status")
        self.assertEqual(200, res.status_code)

    def test_post_unauthorized(self):
        data = dict(
            name="cmp1", impact=1, attributes=[{"name": "a1", "value": "v1"}]
        )
        res = self.client.post(
            "/api/v1/component_status",
            data=json.dumps(data),
            content_type="application/json",
        )
        self.assertEqual(401, res.status_code)

    def test_post_no_incident(self):
        data = dict(
            name="cmp1", impact=1, attributes=[{"name": "a1", "value": "v1"}]
        )
        res = self.client.post(
            "/api/v1/component_status",
            data=json.dumps(data),
            content_type="application/json",
            headers=self.headers,
        )
        self.assertEqual(201, res.status_code)

    def test_post_active_maintenance(self):
        maintenance_id = None
        with self.app.app_context():
            m1 = Incident(
                text="maint",
                components=[
                    Component.find_by_name_and_attributes(
                        name="cmp1", attributes={"a1": "v1"}
                    )
                ],
                impact=0,
            )
            db.session.add(m1)
            db.session.commit()
            maintenance_id = m1.id

            data = dict(
                name="cmp1",
                impact=1,
                attributes=[{"name": "a1", "value": "v1"}],
            )
            res = self.client.post(
                "/api/v1/component_status",
                data=json.dumps(data),
                content_type="application/json",
                headers=self.headers,
            )
            self.assertEqual(201, res.status_code)
            self.assertEqual(maintenance_id, res.json["id"])

            self.assertEqual(0, len(Incident.get_active()))
            maintenance = Incident.get_active_maintenance()
            self.assertIsNotNone(maintenance)
            self.assertIsInstance(maintenance, Incident)
            self.assertEqual(maintenance_id, maintenance.id)

    def test_post_active_maintenance_other_component(self):
        maintenance_id = None
        with self.app.app_context():
            m1 = Incident(
                text="maint",
                components=[
                    Component.find_by_name_and_attributes(
                        name="cmp1", attributes={"a1": "v1"}
                    )
                ],
                impact=0,
            )
            db.session.add(m1)
            db.session.commit()
            maintenance_id = m1.id

            data = dict(
                name="cmp2",
                impact=1,
                attributes=[{"name": "a1", "value": "v1"}],
            )
            res = self.client.post(
                "/api/v1/component_status",
                data=json.dumps(data),
                content_type="application/json",
                headers=self.headers,
            )
            self.assertEqual(201, res.status_code)
            self.assertNotEqual(maintenance_id, res.json["id"])

            self.assertEqual(1, len(Incident.get_active()))
            maintenance = Incident.get_active_maintenance()
            self.assertIsNotNone(maintenance)
            self.assertIsInstance(maintenance, Incident)
            self.assertEqual(maintenance_id, maintenance.id)

    def test_post_active_incident(self):
        inc_id = None
        with self.app.app_context():
            sot = Incident(
                text="inc",
                components=[
                    Component.find_by_name_and_attributes(
                        name="cmp1", attributes={"a1": "v1"}
                    )
                ],
                impact=1,
                system=True,
            )
            db.session.add(sot)
            db.session.commit()
            inc_id = sot.id

            data = dict(
                name="cmp2",
                impact=1,
                attributes=[{"name": "a1", "value": "v1"}],
            )
            res = self.client.post(
                "/api/v1/component_status",
                data=json.dumps(data),
                content_type="application/json",
                headers=self.headers,
            )
            self.assertEqual(201, res.status_code)
            self.assertEqual(inc_id, res.json["id"])

            self.assertEqual(1, len(Incident.get_active()))
            self.assertEqual(inc_id, Incident.get_active()[0].id)

    def test_post_incident_changing_impact(self):
        inc_id = None
        with self.app.app_context():
            sot = Incident(
                text="inc",
                components=[
                    Component.find_by_name_and_attributes(
                        name="cmp1", attributes={"a1": "v1"}
                    )
                ],
                impact=1,
                system=True,
            )
            db.session.add(sot)
            db.session.commit()
            inc_id = sot.id

            new_impact = 2

            data = dict(
                name="cmp1",
                impact=new_impact,
                attributes=[{"name": "a1", "value": "v1"}],
            )
            res = self.client.post(
                "/api/v1/component_status",
                data=json.dumps(data),
                content_type="application/json",
                headers=self.headers,
            )
            self.assertEqual(201, res.status_code)
            self.assertEqual(inc_id, res.json["id"])
            self.assertEqual(new_impact, res.json["impact"])
            self.assertEqual(1, len(Incident.get_active()))
            self.assertEqual(inc_id, Incident.get_active()[0].id)

    def test_post_incident_creating_multiple(self):
        with self.app.app_context():
            impact1 = 1
            impact2 = 2
            data1 = dict(
                name="cmp1",
                impact=impact1,
                attributes=[{"name": "a1", "value": "v1"}],
            )
            res1 = self.client.post(
                "/api/v1/component_status",
                data=json.dumps(data1),
                content_type="application/json",
                headers=self.headers,
            )
            data2 = dict(
                name="cmp2",
                impact=impact2,
                attributes=[{"name": "a1", "value": "v1"}],
            )
            res2 = self.client.post(
                "/api/v1/component_status",
                data=json.dumps(data2),
                content_type="application/json",
                headers=self.headers,
            )
            incidents = Incident.get_active()
            incident1 = next(
                incident for incident in incidents
                if incident.impact == impact1
            )
            incident2 = next(
                incident for incident in incidents
                if incident.impact == impact2
            )
            self.assertEqual(201, res1.status_code)
            self.assertEqual(201, res2.status_code)
            self.assertEqual(incident1.id, res1.json["id"])
            self.assertEqual(incident2.id, res2.json["id"])
            self.assertEqual(2, len(Incident.get_active()))

    def test_post_incident_moving_component(self):
        with self.app.app_context():
            impact1 = 1
            impact2 = 2
            data1 = dict(
                name="cmp1",
                impact=impact1,
                text="API INCIDENT 1",
                attributes=[{"name": "a1", "value": "v1"}],
            )
            res1 = self.client.post(
                "/api/v1/component_status",
                data=json.dumps(data1),
                content_type="application/json",
                headers=self.headers,
            )
            data2 = dict(
                name="cmp2",
                impact=impact2,
                text="API INCIDENT 2",
                attributes=[{"name": "a1", "value": "v1"}],
            )
            res2 = self.client.post(
                "/api/v1/component_status",
                data=json.dumps(data2),
                content_type="application/json",
                headers=self.headers,
            )
            incidents = Incident.get_active()
            incident1 = next(
                incident for incident in incidents
                if incident.impact == impact1
            )
            incident2 = next(
                incident for incident in incidents
                if incident.impact == impact2
            )
            self.assertEqual(201, res1.status_code)
            self.assertEqual(201, res2.status_code)
            self.assertEqual(incident1.id, res1.json["id"])
            self.assertEqual(incident2.id, res2.json["id"])
            self.assertEqual(2, len(Incident.get_active()))

            data3 = dict(
                name="cmp1",
                impact=impact2,
                attributes=[{"name": "a1", "value": "v1"}],
            )
            res3 = self.client.post(
                "/api/v1/component_status",
                data=json.dumps(data3),
                content_type="application/json",
                headers=self.headers,
            )
            self.assertEqual(201, res3.status_code)
            self.assertEqual(1, len(Incident.get_active()))
            self.assertEqual(impact2, res3.json["impact"])
            incident_active = Incident.get_active()[0]
            for inc in Incident.get_all_closed():
                self.assertNotEqual(inc.id, res3.json["id"])
            self.assertEqual(incident_active.id, res3.json["id"])
            # Checking status updates
            comp1 = Component.find_by_name_and_attributes(
                name="cmp1", attributes={"a1": "v1"}
            )
            comp_name = comp1.name
            res_updates = res3.json['updates']
            for item in res_updates:
                if comp_name in item.get("text", ""):
                    break
            else:
                self.assertTrue(
                    False, f"comp name {comp_name} not found in {res_updates}"
                )
