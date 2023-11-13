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
from datetime import datetime

from app import authorization
from app.api import bp
from app.api.schemas.components import ComponentSchema
from app.api.schemas.components import ComponentSearchQueryArgs
from app.api.schemas.components import ComponentStatusArgsSchema
from app.api.schemas.components import IncidentSchema
from app.exporter.requests import after_request, before_request
from app.models import Component
from app.models import Incident
from app.models import db

from flask import current_app
from flask.views import MethodView

from flask_smorest import abort

auth = authorization.auth


@bp.before_request
def before():
    before_request()


@bp.after_request
def after(resp):
    return after_request(resp)


@bp.route("/v1/component_status", methods=["GET", "POST"])
class ApiComponentStatus(MethodView):
    @bp.arguments(ComponentSearchQueryArgs, location="query")
    @bp.response(200, ComponentSchema(many=True))
    def get(self, search_args):
        """Get components

        Query configured components with related incidents.

        Example:

        .. code-block:: console

           curl http://localhost:5000/api/v1/component_status -X GET \\
                -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6Ikp...'


        """
        name = search_args.get("name", "")
        attribute_name = search_args.get("attribute_name", None)
        attribute_value = search_args.get("attribute_value", None)
        attribute = {attribute_name: attribute_value}
        if attribute_name is not None and attribute_value is not None:
            target_component = Component.find_by_name_and_attributes(
                name, attribute
            )
            if target_component is None:
                abort(404, message="Component does not exist")
            return [target_component]
        return db.session.scalars(
            db.select(Component).filter(Component.name.startswith(name))
        ).all()

    @bp.arguments(ComponentStatusArgsSchema)
    @auth.login_required
    @bp.response(201, IncidentSchema)
    def post(self, data):
        """Update component status

        Process component status update and open new incident if required:

        - current active maintenance for the component - do nothing
        - current active incident for the component - do nothing
        - current active incident NOT for the component - add component into
          the list of affected components
        - no active incidents - create new one

        This method requires authorization to be used.

        .. code-block:: console

           curl http://localhost:5000/api/v1/component_status -X POST \\
                -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6pX...' \\
                -H 'content-type:application/json' \\
                -d '{"impact": "minor", "name": "Component 1", \\
                "attributes":[{"name":"region","value":"Reg1"}]}'

        :returns IncidentSchema:
            :class:`~status_dashboard.api.schemas.components.IncidentSchema`
            object
        """
        name = data.get("name", None)
        impact = data.get("impact", 1)
        text = data.get("text", "Incident")
        if impact not in current_app.config["INCIDENT_IMPACTS"].keys():
            return abort(
                400, message="Incident impact is not allowed by configuration"
            )
        attributes = dict()
        # Map attributes from {name:k, value:v} into k:v
        for attr in data.get("attributes", []):
            attributes[attr.get("name")] = attr.get("value")
        target_component = Component.find_by_name_and_attributes(
            name, attributes
        )
        if not target_component:
            abort(400, message="Component not found")
        current_app.logger.debug(target_component)
        maintenance = Incident.get_active_maintenance()
        if maintenance:
            current_app.logger.debug(maintenance)
            if target_component in maintenance.components:
                current_app.logger.debug(
                    "Maintenance is active for the component - not opening "
                    "new incident"
                )
                return maintenance
        incidents = Incident.get_active()
        if incidents:
            incident = incidents[0]
            current_app.logger.debug(incident)
            if target_component not in incident.components:
                # Current active incident is not affecting target_component -
                # add it into the list
                current_app.logger.debug(
                    "Adding component {target_component} into affected "
                    "components of the {incicident}"
                )
                incident.components.append(target_component)
                db.session.commit()
                return incident
            else:
                # For the component incident is already open - do nothing
                current_app.logger.debug(
                    "Active incident for {component} - not opening new "
                    "incident"
                )
                return incident
        else:
            # No active incidents - open new
            current_app.logger.debug("No active incidents - opening new one")
            new_incident = Incident(
                text=text,
                impact=impact,
                start_date=datetime.now(),
                components=[target_component],
            )
            db.session.add(new_incident)
            db.session.commit()
            return new_incident
