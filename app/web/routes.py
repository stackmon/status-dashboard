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

from flask import (
    render_template,
    flash,
    redirect,
    url_for,
    request,
    g,
    jsonify,
    current_app,
)

from app import db

from app.models import Incident
from app.models import IncidentStatus
from app.models import Component


from app.web import bp
from app.web.forms import IncidentForm
from app.web.forms import IncidentUpdateForm
from sqlalchemy import text


@bp.route("/", methods=["GET", "POST"])
@bp.route("/index", methods=["GET", "POST"])
def index():
    stmt_region = text("SELECT DISTINCT value FROM component_attribute WHERE name='region'")
    stmt_category = text("SELECT DISTINCT value FROM component_attribute WHERE name='category'")
    #regions = db.engine.execute(stmt_region).fetchall()
    regions = ("EU-DE", "EU-NL", "Swiss")
    categories = db.engine.execute(stmt_category).fetchall()
    components = Component.query.all()
    incidents = Incident.open()
    return render_template(
        "index.html",
        title="Home",
        regions=regions,
        categories=categories,
        incidents=incidents,
        components=components,
    )
