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
from app.models import IncidentStatus

from testcontainers.postgres import PostgresContainer


class TestBase(TestCase):

    test_config = dict(
        TESTING=True,
        SQLALCHEMY_TRACK_MODIFICATIONS=False  # Ensure this is set to False
    )

    @classmethod
    def setUpClass(cls):
        cls.postgres_container = PostgresContainer()
        cls.postgres_container.start()
        cls.test_config[
            'SQLALCHEMY_DATABASE_URI'
        ] = cls.postgres_container.get_connection_url()

    @classmethod
    def tearDownClass(cls):
        cls.postgres_container.stop()

    def setUp(self):
        self.app = create_app(self.test_config)
        with self.app.app_context():
            Base.metadata.create_all(bind=db.engine)
            db.create_all()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            Base.metadata.drop_all(bind=db.engine)


class TestComponent(TestBase):
    def setUp(self):
        super().setUp()
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
            db.session.commit()

    def test_find_by_name_and_attributes(self):
        with self.app.app_context():
            t1 = Component.find_by_name_and_attributes("cmp1", {"a1": "v1"})
            self.assertEqual("cmp1", t1.name)
            t2 = Component.find_by_name_and_attributes("cmp1", {"a1": "v2"})
            self.assertIsNone(t2)
            t3 = Component.find_by_name_and_attributes("cmp2", {"a2": "v2"})
            self.assertIsNone(t3)

    def test_get_attributes_as_dict(self):
        with self.app.app_context():
            t1 = Component.find_by_name_and_attributes("cmp1", {"a1": "v1"})
            self.assertDictEqual(
                {"a1": "v1", "a2": "v2"}, t1.get_attributes_as_dict()
            )

    def test_all(self):
        with self.app.app_context():
            self.assertTrue(len(Component.all()) > 0)


class TestComponentAttribute(TestBase):
    def setUp(self):
        super().setUp()
        with self.app.app_context():
            db.session.add(ComponentAttribute(name="a1", value="v1"))
            db.session.add(ComponentAttribute(name="a1", value="v2"))
            db.session.add(ComponentAttribute(name="a2", value="v1"))
            db.session.add(ComponentAttribute(name="a3", value="v1"))
            db.session.commit()

    def test_get_unique_values(self):
        with self.app.app_context():
            self.assertEqual(
                ["v1", "v2"], ComponentAttribute.get_unique_values("a1")
            )
            self.assertEqual(
                [], ComponentAttribute.get_unique_values("not_existing")
            )


class TestIncident(TestBase):
    def setUp(self):
        super().setUp()
        with self.app.app_context():
            attr1 = ComponentAttribute(name="a1", value="v1")
            attr2 = ComponentAttribute(name="a2", value="v2")
            attr3 = ComponentAttribute(name="a1", value="v3")
            db.session.add(attr1)
            db.session.add(attr2)
            db.session.add(attr3)
            comp1 = Component(name="cmp1", attributes=[attr1, attr2])
            comp2 = Component(name="cmp2", attributes=[attr3])
            db.session.add(comp1)
            db.session.add(comp2)
            m1 = Incident(text="Maintenance1", impact="0")
            db.session.add(m1)
            i1 = Incident(text="Incident1", impact="1", system=True)
            db.session.add(i1)
            i2 = Incident(
                text="Incident2",
                impact="1",
                end_date=datetime.datetime.now() - datetime.timedelta(days=1),
                components=[comp1],
            )
            db.session.add(i2)
            db.session.commit()
            self.past_id = i2.id

    def test_get_all_active(self):
        with self.app.app_context():
            t1 = Incident.get_all_active()
            self.assertEqual(2, len(t1))

    def test_get_active_maintenance(self):
        with self.app.app_context():
            t1 = Incident.get_active_maintenance()
            self.assertEqual("Maintenance1", t1.text)

    def test_get_active(self):
        with self.app.app_context():
            t1 = Incident.get_active()
            self.assertTrue(len(t1) == 1)
            self.assertEqual("Incident1", t1[0].text)

    def test_get_by_id(self):
        with self.app.app_context():
            t1 = Incident.get_by_id(self.past_id)
            self.assertEqual("Incident2", t1.text)

    def test_get_attributes_by_key(self):
        with self.app.app_context():
            t1 = Incident.get_by_id(self.past_id)
            self.assertEqual(set(["v2"]), t1.get_attributes_by_key("a2"))


class TestIncidentUpdate(TestBase):
    def setUp(self):
        super().setUp()
        with self.app.app_context():
            m1 = Incident(text="Maintenance1", impact="0")
            db.session.add(m1)
            db.session.commit()
            self.inc_id = m1.id

    def test_basic(self):
        with self.app.app_context():
            u1 = IncidentStatus(
                incident_id=self.inc_id, text="msg1", status="status1"
            )
            db.session.add(u1)
            db.session.commit()
            t1 = Incident.get_by_id(self.inc_id)
            self.assertEqual(1, len(t1.updates))
