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
import time

from app.exporter.metrics import (
    record_request,
    record_request_duration,
    record_response_status,
)

from flask import current_app
from flask import request


def before_request():
    if current_app.config["PROMETHEUS_EXPORTER_ENABLED"]:
        request.start_time = time.time()


def after_request(response):
    if current_app.config["PROMETHEUS_EXPORTER_ENABLED"]:
        method = request.method
        endpoint = request.path
        status = response.status_code

        # Checking for an existing start_time attribute in a request
        if hasattr(request, "start_time"):
            duration = time.time() - request.start_time
        else:
            duration = 0.0

        record_request(method, endpoint, status)
        record_request_duration(method, endpoint, status, duration)
        record_response_status(status)

    return response
