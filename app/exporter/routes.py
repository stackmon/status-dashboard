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
from app.exporter import bp
from app.exporter.metrics import record_db_connection_status
from app.exporter.requests import after_request, before_request
from app.models import db

from flask import Response
from flask import current_app


from prometheus_client import REGISTRY, generate_latest

from sqlalchemy import text


def is_db_connected():
    try:
        db.session.execute(text("SELECT 1")).scalar()
        return True
    except Exception as db_error:
        current_app.logger.debug(
            f"Error while checking database connection: {db_error}"
        )
        return False


@bp.before_request
def before():
    before_request()
    connected = is_db_connected()
    record_db_connection_status(connected)


@bp.after_request
def after(resp):
    response = after_request(resp)
    return response


@bp.route("/metrics", methods=["GET"])
def metrics():
    if not current_app.config["PROMETHEUS_EXPORTER_ENABLED"]:
        return Response(
            "Prometheus Exporter is disabled",
            content_type="text/plain",
            status=503,
        )
    return Response(generate_latest(REGISTRY), content_type="text/plain")
