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

from app import db
from app import oauth
from app.models import Incident
from app.models import IncidentStatus
from app.models import Component
from app.web import bp
from app.web.forms import IncidentForm
from app.web.forms import IncidentUpdateForm
from sqlalchemy import text
from flask import abort
from flask import current_app
from flask import redirect
from flask import render_template
from flask import session
from flask import url_for


@bp.route("/", methods=["GET", "POST"])
@bp.route("/index", methods=["GET", "POST"])
def index():
    stmt_category = text(
        "SELECT DISTINCT value FROM component_attribute WHERE name='category'"
    )
    categories_query = db.engine.execute(stmt_category).fetchall()
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
        components_by_cats=components_by_cats,
        all_components=all_components,
    )


@bp.route("/incidents", methods=["GET", "POST"])
def new_incident():
    if "user" not in session:
        abort(401)
    else:
        print(session["user"])

    all_regions = (
        "EU-DE",
        "EU-NL",
        "Swiss",
    )  # Region.query.order_by(Region.name).all()
    all_components = Component.query.order_by(Component.name).all()
    form = IncidentForm()
    form.incident_components.choices = [(s.id, s.name) for s in all_components]
    form.incident_regions.choices = [(s.id, s.name) for s in all_regions]
    if form.validate_on_submit():
        selected_regions = [int(x) for x in form.incident_regions.raw_data]
        selected_components = [
            int(x) for x in form.incident_components.raw_data
        ]
        incident_regions = []
        incident_components = []
        for reg in all_regions:
            if reg.id in selected_regions:
                incident_regions.append(reg)
        for srv in all_components:
            if srv.id in selected_components:
                incident_components.append(srv)

        incident = Incident(
            text=form.incident_text.data,
            impact=form.incident_impact.data,
            start_date=form.incident_start.data,
            regions=incident_regions,
            components=incident_components,
        )
        db.session.add(incident)
        db.session.commit()
    return render_template(
        "create_incident.html", title="Open Incident", form=form
    )


@bp.route("/incidents/<id>", methods=["GET"])
def incident(id):
    incident = Incident.query.filter_by(id=id).first_or_404()
    form = IncidentUpdateForm(id)
    return render_template(
        "incident.html", title="Incident", incident=incident, form=form
    )


@bp.route("/incidents/<id>/update", methods=["POST"])
def post_incident_update(id):
    if "user" not in session:
        abort(401)

    form = IncidentUpdateForm(id)
    if form.validate_on_submit():
        update = IncidentStatus(
            incident_id=id,
            text=form.update_text.data,
            status=form.update_status.data,
        )
        db.session.add(update)
        db.session.commit()
    else:
        print(f"Data validation failed {form.update_text.errors}")
        print(f"Data validation failed {form.update_status.errors}")
    return redirect(url_for("web.incident", id=id))


@bp.route("/login/<name>")
def login(name):
    client = oauth.create_client(name)
    if not client:
        abort(404)

    redirect_uri = url_for("web.auth", name=name, _external=True)
    return client.authorize_redirect(redirect_uri)


@bp.route("/auth/<name>")
def auth(name):
    client = oauth.create_client(name)
    if not client:
        abort(404)

    token = client.authorize_access_token()
    current_app.logger.debug(token)
    user = token.get("userinfo")
    if not user:
        user = client.userinfo()

    current_app.logger.debug(user)

    session["user"] = user
    return redirect("/")


@bp.route("/logout")
def logout():
    # remove the username from the session if it's there
    session.pop("user", None)
    return redirect("/")


def transform_category_name(category_name):
    transformed_name = (
        category_name.replace("_", " ").replace("-", " ").capitalize()
    )
    return transformed_name


def components_by_category(category_name):
    components_by_cat = Component.components_by_category(category_name)
    return components_by_cat
