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
from prometheus_client import Counter
from prometheus_client import Gauge
from prometheus_client import Histogram


request_count = Counter(
    'http_requests_total',
    'Total HTTP Requests',
    ['method', 'endpoint', 'status'],
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP Request Duration',
    ['method', 'endpoint', 'status'],
)

response_status_count = Counter(
    'http_response_status_count',
    'HTTP Response Status Count',
    ['status'],
)

db_connection_gauge = Gauge(
    'db_connection_status',
    'Database Connection Status (1 for connected, 0 for disconnected)',
)


def record_request(method, endpoint, status):
    request_count.labels(
        method=method, endpoint=endpoint, status=status
    ).inc()


def record_request_duration(method, endpoint, status, duration):
    request_duration.labels(
        method=method, endpoint=endpoint, status=status
    ).observe(duration)


def record_response_status(status):
    response_status_count.labels(status=status).inc()


def record_db_connection_status(connected):
    db_connection_gauge.set(1 if connected else 0)
