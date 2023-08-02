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

from app.exporter import bp
from app.exporter.metrics import (
    record_db_connection_status,
    record_request,
    record_request_duration,
    record_response_status,
    record_response_time,
)
from app.models import db

from flask import Response
from flask import current_app
from flask import request

from prometheus_client import REGISTRY, generate_latest

from sqlalchemy import text


def before_request():
    if current_app.config["PROMETHEUS_EXPORTER_ENABLED"]:
        request.start_time = time.time()


@bp.after_request
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

        response_time = float(response.headers.get("X-Response-Time", 0.0))

        record_request(method, endpoint, status)
        record_request_duration(method, endpoint, status, duration)
        record_response_status(status)
        record_response_time(response_time)

        connected = is_db_connected()
        record_db_connection_status(connected)

    return response


def is_db_connected():
    try:
        db.session.execute(text("SELECT 1")).scalar()
        return True
    except Exception as db_error:
        current_app.logger.debug(
            f"Error while checking database connection: {db_error}"
        )
        return False


@bp.route("/metrics", methods=["GET"])
def metrics():
    if not current_app.config["PROMETHEUS_EXPORTER_ENABLED"]:
        return Response(
            "Prometheus Exporter is disabled",
            content_type="text/plain",
            status=503,
        )
    return Response(generate_latest(REGISTRY), content_type="text/plain")
