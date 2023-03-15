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

from app.api import bp
from app.api.schemas.components import ComponentSchema
from app.api.schemas.components import ComponentSearchQueryArgs
from app.api.schemas.components import IncidentPostArgs
from app.models import Component
from app.models import Incident
from app.models import db

from flask.views import MethodView

from flask_smorest import abort


@bp.route("/api/v1/components_status", methods=["GET", "POST"])
class ApiComponentsStatus(MethodView):
    @bp.arguments(ComponentSearchQueryArgs, location="query")
    @bp.response(200, ComponentSchema(many=True))
    def get(self, search_args):
        name = search_args.get("name", "")
        attribute_name = search_args.get("attribute_name", None)
        attribute_value = search_args.get("attribute_value", None)
        attribute = {attribute_name: attribute_value}
        if attribute_name is not None and attribute_value is not None:
            target_component = Component.find_by_name_and_attributes(
                name,
                attribute
            )
            if target_component is None:
                abort(404, message="Component does not exist")
            return [target_component]
        return Component.query.filter(Component.name.startswith(name)).all()

    @bp.arguments(ComponentSearchQueryArgs, location="query")
    @bp.arguments(IncidentPostArgs, location="form")
    @bp.response(200, ComponentSchema(many=True))
    def post(self, query_args, form_args):
        name = query_args.get("name", None)
        attribute_name = query_args.get("attribute_name", None)
        attribute_value = query_args.get("attribute_value", None)
        attribute = {attribute_name: attribute_value}
        if all(v is not None for v in [name, attribute_name, attribute_value]):
            target_component = Component.find_by_name_and_attributes(
                name,
                attribute
            )
            if target_component is None:
                abort(404, message="Component does not exist")
            incident = Incident(
                text=form_args.get("text", None),
                impact=form_args.get("impact", None),
                start_date=datetime.now(),
                components=[target_component],
            )
            db.session.add(incident)
            db.session.commit()
            return [target_component]
        abort(404, message="Wrong arguments passed to")
