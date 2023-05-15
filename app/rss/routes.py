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

from app.api.schemas.components import ComponentSchema
from app.models import Component
from app.rss import bp

from feedgen.feed import FeedGenerator

from flask import escape
from flask import make_response
from flask import request


def sorted_incidents(incidents):
    sorted_list = []
    for incident in incidents:
        sorted_list.append(incident)
    sorted_list = sorted(
        sorted_list,
        key=lambda x: datetime.strptime(
            x["start_date"], "%Y-%m-%d %H:%M"
        ),
        reverse=True
    )
    last_10_incidents = sorted_list[:10]
    return last_10_incidents


@bp.route("/rss/")
def rss():
    region = request.args.get("mt", "")
    component_name = request.args.get("srv", "")
    attr_name = "region"
    attr_value = region
    attribute = {attr_name: attr_value}
    incorr_req = "Status Dashboard RSS feed\n"\
        "Please read the documentation to\n"\
        "make the correct request"
    if component_name and not region:
        response = make_response(escape(incorr_req))
        response.headers["Content-Type"] = "text/plain"
        response.status_code = 404
        return response
    if component_name and region:
        component = Component.find_by_name_and_attributes(
            component_name,
            attribute
        )
        if not component:
            content = f"Component: {component_name} is not found"
            response = make_response(escape(content))
            response.headers["Content-Type"] = "text/plain"
            response.status_code = 404
            return response
        components = [component]
    elif region and not component_name:
        components = Component.find_by_attribute(attribute)
        if not components:
            content = (
                f"Not components found for {region}\n"
                "Check the correctness of the request"
            )
            response = make_response(escape(content))
            response.headers["Content-Type"] = "text/plain"
            response.status_code = 404
            return response
    #
    # RSS feed generator
    # the generator uses a data dump according to the schema Component
    # as data, the schemas are described in the:
    # "app/api/schemas/components.py"
    #
    if region:
        fg = FeedGenerator()
        if component_name:
            fg.title(
                f"{component_name} ({region}) - Incidents"
            )
            fg.link(
                href=f"{request.url_root}"
                f"rss/?mt={region}&srv={component_name}",
                rel="self"
            )
            fg.description(
                f"{region} - Incidents"
            )
        else:
            fg.title(
                f"{region} - Incidents"
            )
            fg.link(
                href=f"{request.url_root}rss/?mt={region}",
                rel="self"
            )
            fg.description(
                f"{region} - Incidents"
            )
        #
        # This part is needed to be able to
        # make a request without component_name
        # and get all incidents for the specified region
        #
        incidents = []
        for component in components:
            component_data = ComponentSchema().dump(component)
            incidents.extend(component_data["incidents"])

        for incident in reversed(sorted_incidents(incidents)):
            if incident["end_date"] is None or datetime.strptime(
                incident["end_date"], "%Y-%m-%d %H:%M"
            ) <= datetime.today():
                fe = fg.add_entry()
                fe.title(incident["text"])
                start_date = datetime.strptime(
                    incident["start_date"],
                    "%Y-%m-%d %H:%M"
                ).astimezone()
                if incident["end_date"]:
                    end_date = datetime.strptime(
                        incident["end_date"],
                        "%Y-%m-%d %H:%M"
                    ).astimezone()
                else:
                    end_date = None
                content_string = f"Incident impact: {incident['impact']}, \
                        Incident start date: {start_date}, \
                        incident end date: {end_date}"
                #
                # "updates" exist as a sublist for the incident,
                # schemes are described in the file:
                #  "app/api/schemas/components.py"
                # look at the "class IncidentSchema(Schema):"
                # and class "IncidentStatusSchema(Schema):"
                #
                if incident["updates"]:
                    for update in incident["updates"]:
                        update_timestamp = datetime.strptime(
                            update["timestamp"],
                            "%Y-%m-%d %H:%M"
                        ).astimezone()
                    content_string += f"\n \
                                        Update: {update['text']}, \
                                        Update timestamp: {update_timestamp}"
                    fe.pubDate(update_timestamp)
                else:
                    fe.pubDate(start_date)
                fe.content(f"{content_string}")

        rss_string = fg.rss_str(pretty=True).decode("utf-8")
        response = make_response(rss_string)
        response.headers["Content-Type"] = "application/xml"
        return response
    elif not region and not component_name:
        response = make_response(escape(incorr_req))
        response.headers["Content-Type"] = "text/plain"
        response.status_code = 404
        return response
    else:
        response = make_response(escape(incorr_req))
        response.headers["Content-Type"] = "text/plain"
        response.status_code = 404
        return response
