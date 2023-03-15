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
from flask import request, jsonify
from flask_restful import Resource, reqparse
from app import db
from app.models import Component
from app.models import Incident


def create_incident_parser():
    parser = reqparse.RequestParser()
    parser.add_argument(
        "text",
        action="append",
        required=True,
        location="json",
    )
    parser.add_argument(
        "impact",
        help="Bad choice: {error_msg}",
        type=str,
        choices=["maintenance", "minor", "major", "outage"],
        required=True,
        location="json",
    )
    parser.add_argument(
        "components",
        action="append",
        required=False,
        location="json",
    )
    return parser

def filter_incident(incidents: list, incident_id: int):
    for incident in incidents:
        if incident.id == incident_id:
            target_incident = incident
    return target_incident

def incident_does_exist(incidents: list, incident_id: int):
    incident_ids = []
    for incident in incidents:
        incident_ids.append(incident.id)
    if incident_id in incident_ids:
        exists = True
    else:
        exists = False
    return exists


class ApiIncidents(Resource):
    def get(self):
        if request.method == "GET":
            incidents=Incident.query.all()
            return jsonify([incident.serialize for incident in incidents])
        return jsonify(message="Method not allowed"), 405

    def post(self):
        class ReqparseError(ValueError):
            def __str__(self):
                return "Did not enter true value for one of the arguments"
        all_components = Component.query.order_by(Component.id).all()
        parser = create_incident_parser()
        args = parser.parse_args()
        try:
            comps_string = str(args["components"][0])
            try:
                selected_components = list(map(int, comps_string.split(",")))
                raise ReqparseError
            except ReqparseError as error:
                print(error)
            incident_components = []
            for component in all_components:
                if component.id in selected_components:
                    incident_components.append(component)
            incident = Incident(
                text = str(args["text"]),
                impact = str(args["impact"]),
                components = incident_components,
                start_date = datetime.datetime.now()
            )
            db.session.add(incident)
            db.session.commit()
            return {"message": f"Incident: {incident} has been posted"}, 200
        except ReqparseError as error:
            print(error)

class ApiIncident(Resource):
    def get(self, incident_id):
        incidents = Incident.query.all()
        if incident_id == 0:
            return jsonify([incident.serialize for incident in incidents])
        if incident_does_exist(incidents, incident_id) is True:
            target_incident = Incident.query.get(incident_id)
            return jsonify(target_incident.serialize)
        return {"message": "Incident does not exist"}, 404

    def delete(self, incident_id):
        incidents = Incident.query.all()
        if incident_does_exist(incidents, incident_id) is True:
            target_incident = Incident.query.get(incident_id)
            db.session.delete(target_incident)
            db.session.commit()
            return {"message": f"Incident with id: {incident_id} has been deleted"}, 204
        return {"message": "Incident does not exist"}, 404
