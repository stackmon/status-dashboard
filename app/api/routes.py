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

from app.api import authorization
from app.api import bp
from app.api.schemas.components import ComponentSchema
from app.api.schemas.components import ComponentSearchQueryArgs
from app.api.schemas.components import ComponentStatusArgsSchema
from app.api.schemas.components import IncidentSchema
from app.models import Component
from app.models import Incident
from app.models import db

from flask import current_app
from flask.views import MethodView

from flask_smorest import abort

auth = authorization.auth


@bp.route("/v1/component_status", methods=["GET", "POST"])
class ApiComponentStatus(MethodView):
    @bp.arguments(ComponentSearchQueryArgs, location="query")
    @bp.response(200, ComponentSchema(many=True))
    def get(self, search_args):
        """Get components

        Get configured components with related incidents
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
        return Component.query.filter(Component.name.startswith(name)).all()

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

        :returns IncidentSchema: Incident object
        """
        name = data.get("name", None)
        impact = data.get("impact", "minor")
        attributes = dict()
        # Map attributes from {name:k, value:v} into k:v
        for attr in data.get("attributes", []):
            attributes[attr.get("name")] = attr.get("value")
        target_component = Component.find_by_name_and_attributes(
            name, attributes
        )
        if not target_component:
            abort(409, message="Component not found")
        current_app.logger.debug(target_component)
        maintenance = Incident.get_active(impact="maintenance").first()
        if maintenance:
            current_app.logger.debug(maintenance)
            if target_component in maintenance.components:
                current_app.logger.debug(
                    "Maintenance is active for the component - not opening "
                    "new incident"
                )
                return maintenance
        incident = Incident.get_active().first()
        if incident:
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
                return None
        else:
            # No active incidents - open new
            current_app.logger.debug("No active incidents - opening new one")
            new_incident = Incident(
                text=f"{impact} Incident",
                impact=impact,
                start_date=datetime.now(),
                components=[target_component],
            )
            db.session.add(new_incident)
            db.session.commit()
            return new_incident
