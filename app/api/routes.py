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
from app.models import Component
from app.models import Incident
from app.models import IncidentStatus
from app.models import db

from flask import current_app
from flask.views import MethodView

from flask_smorest import abort

auth = authorization.auth


def inc_by_impact(incidents, impact):
    incident_match = next(
        (incident for incident in incidents if incident.impact == impact),
        None
    )
    return incident_match


def add_component_to_incident(target_component, incident):
    current_app.logger.debug(
        f"Add {target_component} to the incident: {incident}"
    )
    incident.components.append(target_component)
    db.session.commit()
    return incident


def create_new_incident(target_component, impact, text):
    new_incident = Incident(
        text=text,
        impact=impact,
        start_date=datetime.now(),
        components=[target_component],
        system=True,
    )
    db.session.add(new_incident)
    db.session.commit()
    return new_incident


def update_incident_status(incident, text_status, status="SYSTEM"):
    update = IncidentStatus(
        incident_id=incident.id,
        text=text_status,
        status=status,
    )
    current_app.logger.debug(f"UPDATE_STATUS: {text_status}")
    db.session.add(update)


def handling_incidents(
    target_component,
    impact,
    impacts,
    src_incident,
    dst_incident=None,
    text=None
):
    if len(src_incident.components) == 1 and dst_incident:
        current_app.logger.debug(f"Component moved to: '{dst_incident.text}'")
        current_app.logger.debug(f"{src_incident.text} CLOSED")
        update_incident_status(
            src_incident,
            (
                f"{target_component} moved to: '{dst_incident.text}', "
                "incident closed by system"
            )
        )
        update_incident_status(
            dst_incident,
            f"{target_component} moved from {src_incident.text}"
        )
        src_incident.end_date = datetime.now()
        dst_incident.components.append(target_component)
        db.session.commit()
        return dst_incident
    elif len(src_incident.components) == 1 and not dst_incident:
        current_app.logger.debug(
            f"Component: {target_component} is present in the incident: "
            f"'{src_incident.text}'"
        )
        current_app.logger.debug(
            "Requested impact higher than current, "
            f"changing the impact from: {impacts[src_incident.impact].key}"
            f"to {impacts[impact].key}"
        )
        update_incident_status(
            src_incident,
            (
                f"Impact changed: from {impacts[src_incident.impact].key} "
                f"to {impacts[impact].key}"
            )
        )
        src_incident.impact = impact
        db.session.commit()
        return src_incident
    elif len(src_incident.components) > 1 and dst_incident:
        current_app.logger.debug(
            f"{target_component} moved from {src_incident.text} to "
            f"{dst_incident.text}"
        )
        update_incident_status(
            src_incident,
            f"{target_component} moved to {dst_incident.text}"
        )
        update_incident_status(
            dst_incident,
            f"{target_component} moved from {src_incident.text}"
        )
        src_incident.components.remove(target_component)
        dst_incident.components.append(target_component)
        db.session.commit()
        return dst_incident
    elif len(src_incident.components) > 1 and not dst_incident:
        current_app.logger.debug(
            "No active incidents with requested impact - opening new one"
        )
        return create_new_incident(target_component, impact, text)
    else:
        current_app.logger.debug("Unexpected ERROR")


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
        - current active incident for the component and requested
          impact > current impact - run handling:

          If a component exists in an incident, but the requested
          impact is higher than the current one, then the component
          will be moved to another incident if it exists with the
          requested impact, otherwise a new incident will be created
          and the component will be moved to the new incident.
          If there is only one component in an incident, and an
          incident with the requested impact does not exist,
          then the impact of the incident will be changed to a higher
          one, otherwise the component will be moved to an existing
          incident with the requested impact, and the current incident
          will be closed by the system.
          The movement of a component and the closure of an incident
          will be reflected in the incident statuses.

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
        impacts = current_app.config["INCIDENT_IMPACTS"]
        maintenance = Incident.get_active_maintenance()
        if maintenance:
            current_app.logger.debug(maintenance)
            if target_component in maintenance.components:
                current_app.logger.debug(
                    "Maintenance is active for the component - not opening "
                    "new incident"
                )
                return maintenance
        incidents_by_user = Incident.get_active_m()
        for incident in incidents_by_user:
            if target_component in incident.components and \
                impact <= incident.impact:
                current_app.logger.debug(
                    "Incident is active for the component, "
                    "requested impact equal or less - not modifying "
                    "or opening new incident"
                )
                return incident
        incidents = Incident.get_active()
        if not incidents:
            current_app.logger.debug("No active incidents - opening new one")
            return create_new_incident(target_component, impact, text)

        component_not_found = not any(
            target_component in incident.components for incident in incidents
        )
        if component_not_found:
            incident_match = inc_by_impact(incidents, impact)
            if incident_match:
                return add_component_to_incident(
                    target_component, incident_match
                )
            else:
                current_app.logger.debug(
                    f"{target_component} not found in any incident, "
                    "create a new incident"
                )
                """The incident is not affecting target_component,
                the requested impact doesn't match - open
                a new incident
                """
                return create_new_incident(target_component, impact, text)
        else:
            incident_match = inc_by_impact(incidents, impact)
            for incident in incidents:
                if target_component in incident.components:
                    if impact > incident.impact:
                        return (
                            handling_incidents(
                                target_component,
                                impact,
                                impacts,
                                incident,
                                incident_match,
                                text
                            )
                        )
                    else:
                        # For the component incident is already open -
                        # do nothing
                        current_app.logger.debug(
                            f"Active incident for {target_component} - "
                            "not modifying or opening new incident"
                        )
                        return incident
