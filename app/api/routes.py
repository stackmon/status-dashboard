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
""" Start _ Old code: 
# from .resources import incidents, components
# 
# 
# def initialize_routes(api):
#     api.add_resource(incidents.ApiIncidents, '/api/v1/incidents')
#     api.add_resource(incidents.ApiActiveMaintenance, '/api/v1/incidents/active_maintenance')
#     api.add_resource(incidents.ApiActiveIncident, '/api/v1/incidents/active_incident')
#     api.add_resource(incidents.ApiIncident, "/api/v1/incidents/<str:component>")
#     api.add_resource(components.ApiInfo, "/api/v1/info")
#     api.add_resource(components.ApiComponents, "/api/v1/components")
#     api.add_resource(components.UniqueComponents, "/api/v1/unique_components")
End _ Old code """

from app.models import db
from app import oauth
from app.models import Component
from app.models import ComponentAttribute
from app.models import Incident
from app.models import IncidentStatus
from app.models import auth_required
from app.api import bp

from flask import Response, request, jsonify
from flask.views import MethodView
from app.api.schemas.components import ComponentSchema


@bp.route("/api/v1/components", methods=["GET"])
class ApiComponents(MethodView):
    @bp.response(200, ComponentSchema(many=True))
    def get(self):
        return Component.query.order_by(Component.id).all()


@bp.route("/api/v1/incidents", methods=["GET"])
def incidents():
    if request.method == "GET":
        incidents=Incident.query.all()
        return jsonify([incident.serialize for incident in incidents])
    return jsonify(message="Method not allowed"), 405


@bp.route("/api/v1/incidents/active_maintenance", methods=["GET"])
def get_maintenance():
    if request.method == "GET":
        active_maintenance = Incident.get_active("maintenance")
        return jsonify([maintenance.serialize for maintenance in active_maintenance])
    return jsonify(message="Method not allowed"), 405


@bp.route("/api/v1/incidents/active_incident", methods=["GET"])
def get_incidents():
    if request.method == "GET":
        active_incident = Incident.get_active("incident")
        return jsonify([incident.serialize for incident in active_incident])
    return jsonify(message="Method not allowed"), 405
