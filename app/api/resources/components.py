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

from flask import request, jsonify
from flask_restful import Resource
from app.models import Component


class ApiComponents(Resource):
    def get(self):
        if request.method == "GET":
            all_components = Component.query.order_by(Component.id).all()
            return jsonify([component.serialize for component in all_components])
        return jsonify(message="Method not allowed"), 405


class UniqueComponents(Resource):
    def get(self):
        if request.method == "GET":
            components = Component.query.distinct(Component.id).all()
            components_ids = [component.id for component in components]
            return jsonify(components_ids)
        return jsonify(message="Method not allowed"), 405

class ApiInfo(Resource):
    def get(self):
        return {
            "Code Range and Category": {
                "2xx": "Successful operation",
                "3xx": "Redirection",
                "4xx": "Client error",
                "5xx": "Server error"
            }
        }
