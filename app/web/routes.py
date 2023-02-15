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
    categories_query = db.engine.execute(stmt_category).fetchall()
    #regions = db.engine.execute(stmt_region).fetchall()
    regions = ("EU-DE", "EU-NL", "Swiss")

    categories_list = []
    for category in categories_query:
        category = category[0]
        categories_list += [category]
    categories_list = sorted(categories_list, reverse=False)

    categories = {}
    for category in categories_list:
        categories[category] = transform_category_name(category)
    all_components = Component.query.all()
    components = {}
    for component in all_components:
        components[component.id] = component.name

    incidents = Incident.open()
    
    components_by_cats = {}
    for category in categories_list:
        components_by_cats[category] = components_by_category(category)

    return render_template(
        "index.html",
        title="Home",
        regions=regions,
        categories=categories,
        incidents=incidents,
        components=components,
        components_by_cats = components_by_cats,
        all_components = all_components,
    )

def transform_category_name(category_name):
    transformed_name = category_name.replace("_", " ").replace("-", " ").capitalize()
    return transformed_name

def components_by_category(category_name):
    components_by_cat = Component.components_by_category(category_name)
    return components_by_cat
