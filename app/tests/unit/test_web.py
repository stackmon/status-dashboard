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
from unittest import TestCase

from app import create_app
from app import db
from app.models import Base
from app.models import Component
from app.models import ComponentAttribute
from app.models import Incident


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


class TestWeb(TestBase):
    def setUp(self):
        super().setUp()

        self.client = self.app.test_client()

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

            inc1 = Incident(
                text="inc",
                components=[comp1],
                impact=1,
                end_date=datetime.datetime.now() - datetime.timedelta(days=1),
            )
            db.session.add(inc1)
            db.session.commit()
            self.incident_id = inc1.id

    def test_get_root(self):
        res = self.client.get("/")
        self.assertEqual(200, res.status_code)

    def test_get_incidents_no_auth(self):
        res = self.client.get("/incidents")
        self.assertEqual(401, res.status_code)

    def test_get_incident(self):
        res = self.client.get(f"/incidents/{self.incident_id}")
        self.assertEqual(200, res.status_code)
