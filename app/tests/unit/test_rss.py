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


class TestRSS(TestBase):
    def setUp(self):
        super().setUp()

        self.client = self.app.test_client()

        with self.app.app_context():
            attr1 = ComponentAttribute(name="region", value="Region1")
            attr2 = ComponentAttribute(name="region", value="Region2")
            db.session.add(attr1)
            db.session.add(attr2)
            comp1 = Component(name="Component1", attributes=[attr1])
            comp2 = Component(name="Component2", attributes=[attr2])
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
            db.session.add(
                Incident(
                    text="inc2",
                    components=[comp2],
                    impact=2,
                    end_date=datetime.datetime.now()
                    - datetime.timedelta(days=2),
                )
            )
            db.session.commit()

    def test_get_regandcomp_200(self):
        res = self.client.get(
            "http://127.0.0.1:5000/rss/?mt=Region1&srv=Component1"
        )
        self.assertEqual(200, res.status_code)
        rss_content = res.get_data(as_text=True)
        self.assertIn("Component1 (Region1) - Incidents", rss_content)
        self.assertIn("Incident impact: 1", rss_content)
        self.assertNotIn("Component2", rss_content)
        self.assertNotIn("Incident impact: 2", rss_content)

    def test_get_regandcomp_404(self):
        res = self.client.get(
            "http://127.0.0.1:5000/rss/?mt=Region11&srv=Component11"
        )
        self.assertEqual(404, res.status_code)
        rss_content = res.get_data(as_text=True)
        self.assertIn("Component: Component11 is not found", rss_content)

    def test_get_region_200(self):
        res = self.client.get(
            "http://127.0.0.1:5000/rss/?mt=Region1"
        )
        self.assertEqual(200, res.status_code)
        rss_content = res.get_data(as_text=True)
        self.assertIn("Region1 - Incidents", rss_content)

    def test_get_region_404(self):
        res = self.client.get(
            "http://127.0.0.1:5000/rss/?mt=Region12"
        )
        self.assertEqual(404, res.status_code)
        rss_content = res.get_data(as_text=True)
        self.assertIn("Not components found for Region12", rss_content)
