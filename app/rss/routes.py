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
import os
from datetime import datetime

from app.api.schemas.components import ComponentSchema
from app.models import Component
from app.rss import bp

from feedgen.feed import FeedGenerator

from flask import Response
from flask import request

import pytz


def sorted_incidents(incidents):
    none_end_date_list = []
    sorted_list = []
    limited_incidents = []
    for incident in incidents:
        if incident["end_date"] is None:
            none_end_date_list.append(incident)
        else:
            sorted_list.append(incident)
    sorted_list = sorted(
        sorted_list,
        key=lambda x: datetime.strptime(
            x["start_date"], "%Y-%m-%d %H:%M"
        ),
        reverse=True
    )
    sorted_list = sorted_list[:9]
    limited_incidents.extend(none_end_date_list)
    limited_incidents.extend(sorted_list)
    last_10_incidents = limited_incidents[:10]
    return last_10_incidents


@bp.route("/rss/")
def rss():
    timezone = os.getenv("TZ", "UTC")
    tz = pytz.timezone(timezone)
    region = request.args.get("mt", "")
    component_name = request.args.get("srv", "")
    attr_name = "region"
    attr_value = region
    attribute = {attr_name: attr_value}
    if not component_name and not region:
        return (
            "<html><body>"
            "Status Dashboard RSS feed<br>"
            "Please read the documentation to<br>"
            "make correct request"
            "</body></html>",
            404
        )
    if component_name:
        component = Component.find_by_name_and_attributes(
            component_name,
            attribute
        )
        if not component:
            return f"Component: {component_name} is not found", 404
        components = [component]
    else:
        components = Component.find_by_attribute(attribute)
        if not components:
            return (f"Not components found for {region}<br>"
                    f"Check the correctness of the request", 404
            )
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
            start_date = tz.localize(
                datetime.strptime(
                    incident["start_date"],
                    "%Y-%m-%d %H:%M"
                )
            )
            if incident["end_date"]:
                end_date = tz.localize(
                    datetime.strptime(
                        incident["end_date"],
                        "%Y-%m-%d %H:%M"
                    )
                )
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
                    update_timestamp = tz.localize(
                        datetime.strptime(
                            update["timestamp"],
                            "%Y-%m-%d %H:%M"
                        )
                    )
                content_string += f"\n \
                                    <div class='update'> \
                                    Update: {update['text']}, \
                                    Update timestamp: {update_timestamp} \
                                    </div>"
                fe.pubDate(update_timestamp)
            else:
                fe.pubDate(start_date)
            fe.content(f"<div class='item_desc'>{content_string}</div>")

    rss_string = fg.rss_str(pretty=True).decode("utf-8")
    rss_string = rss_string.replace("<span", "<div")
    rss_string = rss_string.replace("</span>", "</div>")
    rss_string = rss_string.replace(
        "<pre",
        '<pre style="white-space: pre-wrap; font-family: monospace"'
    )
    return Response(rss_string, mimetype="application/xml")
