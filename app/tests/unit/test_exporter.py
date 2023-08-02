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
from unittest import TestCase
from unittest.mock import patch

from app import create_app, db
from app.exporter.metrics import db_connection_gauge
from app.exporter.metrics import record_db_connection_status
from app.exporter.metrics import record_request
from app.exporter.metrics import record_request_duration
from app.exporter.metrics import record_response_status
from app.exporter.metrics import record_response_time
from app.exporter.metrics import request_count
from app.exporter.metrics import response_status_count
from app.models import Base

from prometheus_client import REGISTRY as prometheus_registry


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


class PrometheusExporterTestCase(TestBase):
    def setUp(self):
        super().setUp()
        self.client = self.app.test_client()

    def test_metrics_endpoint_disabled(self):
        with patch.dict(
            self.app.config, {"PROMETHEUS_EXPORTER_ENABLED": False}
        ):
            response = self.client.get("/metrics")
        self.assertEqual(response.status_code, 503)
        self.assertIn(b"Prometheus Exporter is disabled", response.data)

    def test_metrics_endpoint_enabled(self):
        with patch.dict(
            self.app.config, {"PROMETHEUS_EXPORTER_ENABLED": True}
        ):
            response = self.client.get("/metrics")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"http_requests_total", response.data)
        self.assertIn(b"http_request_duration_seconds", response.data)

    def test_record_request(self):
        method = "GET"
        endpoint = "/test_record_request"
        status = 200
        record_request(method, endpoint, status)
        self.assertEqual(
            request_count.labels(
                method=method,
                endpoint=endpoint,
                status=str(status)
            )._value.get(), 1)

    def test_record_request_duration(self):
        method = "GET"
        endpoint = "/test_record_request_duration"
        status = 200
        duration = 4.5

        record_request_duration(method, endpoint, status, duration)

        metric_samples = prometheus_registry.collect()

        expected_bucket_value = 1.0
        expected_sum_duration = duration

        http_request_duration_buckets = []
        sum_duration_metric = None

        for metric in metric_samples:
            for sample in metric.samples:
                if sample.name == "http_request_duration_seconds_bucket":
                    http_request_duration_buckets.append(sample)
                elif (
                    sample.name == "http_request_duration_seconds_sum" and
                    sample.value == duration
                ):
                    sum_duration_metric = sample

        for sample in http_request_duration_buckets:
            if sample.labels.get("le") == "5.0":
                le_5_bucket = sample
                break

        self.assertIsNotNone(le_5_bucket)
        self.assertEqual(le_5_bucket.value, expected_bucket_value)
        self.assertEqual(sum_duration_metric.value, expected_sum_duration)

    def test_record_response_status(self):
        status = "500"
        count = 3
        for _ in range(count):
            record_response_status(status)

        self.assertEqual(
            response_status_count.labels(status=status)._value.get(), count
        )

    def test_record_response_time(self):
        time = 1.5
        record_response_time(time)

        metric_samples = prometheus_registry.collect()
        response_time_seconds_buckets = []
        sum_response_time_metric = None
        expected_bucket_value = 1.0
        expected_sum_time = time
        for metric in metric_samples:
            for sample in metric.samples:
                if sample.name == "http_response_time_seconds_bucket":
                    response_time_seconds_buckets.append(sample)
                elif (
                    sample.name == "http_response_time_seconds_sum" and
                    sample.value == time
                ):
                    sum_response_time_metric = sample

        for sample in response_time_seconds_buckets:
            if sample.labels.get("le") == "2.5":
                le_2_5_bucket = sample
                break

        self.assertIsNotNone(le_2_5_bucket)
        self.assertEqual(le_2_5_bucket.value, expected_bucket_value)
        self.assertEqual(sum_response_time_metric.value, expected_sum_time)

    def test_record_db_connection_status_connected(self):
        record_db_connection_status(connected=True)
        self.assertEqual(db_connection_gauge._value.get(), 1)

    def test_record_db_connection_status_disconnected(self):
        record_db_connection_status(connected=False)
        self.assertEqual(db_connection_gauge._value.get(), 0)
