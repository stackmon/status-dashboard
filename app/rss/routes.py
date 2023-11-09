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

from app.models import Component
from app.models import ComponentAttribute
from app.models import Incident
from app.rss import bp

from feedgen.feed import FeedGenerator

from flask import current_app
from flask import make_response
from flask import request

from markupsafe import escape


@bp.route("/rss/")
def rss():
    region = request.args.get("mt", "")
    component_name = request.args.get("srv", "")
    attr_name = "region"
    attr_value = region
    attribute = {attr_name: attr_value}
    incorr_req = (
        "Status Dashboard RSS feed\n"
        "Please read the documentation to\n"
        "make the correct request"
    )
    incidents = list()
    if component_name and not region:
        return make_response(escape(incorr_req), 404)
    if component_name and region:
        component = Component.find_by_name_and_attributes(
            component_name, attribute
        )
        if not component:
            content = f"Component: {escape(component_name)} is not found"
            return make_response(escape(content), 404)
        incidents = component.incidents
    elif region:
        supported_vals = ComponentAttribute.get_unique_values(attr_name)
        if attr_value not in supported_vals:
            return make_response(
                f"{escape(attr_value)} is not a supported region", 404
            )
        incidents = Incident.get_view_by_component_attribute(
            attr_name, attr_value
        ).fetchmany(size=10)
    elif not region and not component_name:
        return make_response(escape(incorr_req), 404)
    #
    # RSS feed generator
    fg = FeedGenerator()
    if component_name:
        fg.title(f"{component_name} ({region}) - Incidents | Status Dashboard")
        fg.link(
            href=f"{request.url_root}"
            f"rss/?mt={region}&srv={component_name}",
            rel="self",
        )
        fg.description(f"{region} - Incidents")
    else:
        fg.title(f"{region} - Incidents | Status Dashboard")
        fg.link(href=f"{request.url_root}rss/?mt={region}", rel="self")
        fg.description(f"{region} - Incidents")
    if incidents:
        date_format = "%Y-%m-%d %H:%M %Z"
        for incident in incidents:
            fe = fg.add_entry()
            fe.title(incident.text)
            content = list()
            if incident.updates:
                for update in sorted(
                    incident.updates,
                    key=lambda update: update.timestamp,
                    reverse=True,
                ):
                    # append empty line before every update
                    content.append(
                        f"<small>{update.timestamp.strftime(date_format)}"
                        "</small><br>"
                        f"<strong>{update.status} - </strong>{update.text}",
                    )
                    content.append("<br>")
                fe.pubDate(update.timestamp.astimezone())
            else:
                fe.pubDate(incident.start_date.astimezone())
            content.extend(
                [
                    "Incident impact: "
                    + current_app.config["INCIDENT_IMPACTS"][
                        incident.impact
                    ].key,
                    "Incident has started on: "
                    f"{incident.start_date.strftime(date_format)}",
                ]
            )
            if incident.end_date:
                content.append(
                    "Incident end date: "
                    f"{incident.end_date.strftime(date_format)}"
                )
            content.append("<br>")
            content.append(
                "We apologize for the inconvenience and will share an update "
                "once we have more information.",
            )
            # Join all content elements by a line break
            fe.content("<br>".join(content))
            fe.link(href=f"{request.url_root}incidents/{incident.id}")
            fe.id(f"{request.url_root}incidents/{incident.id}")

    response = make_response(fg.rss_str())
    response.headers["Content-Type"] = "application/rss+xml"
    return response
