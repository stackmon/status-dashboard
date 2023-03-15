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

from app.models import db
from app import oauth
from app.models import Component
from app.models import ComponentAttribute
from app.models import Incident
from app.models import IncidentStatus
from app.models import auth_required
from app.web import bp
from app.web.forms import IncidentForm
from app.web.forms import IncidentUpdateForm

from flask import abort
from flask import current_app
from flask import redirect
from flask import render_template
from flask import session
from flask import url_for


@bp.route("/", methods=["GET"])
@bp.route("/index", methods=["GET"])
def index():

    return render_template(
        "index.html",
        title="Status Dashboard",
        components=Component,
        component_attributes=ComponentAttribute,
        incidents=Incident,
    )


@bp.route("/incidents", methods=["GET", "POST"])
@auth_required
def new_incident(current_user):
    """Create new Incident"""
    all_components = Component.query.order_by(Component.name).all()
    form = IncidentForm()
    form.incident_components.choices = [(c.id, c) for c in all_components]

    if form.validate_on_submit():
        selected_components = [
            int(x) for x in form.incident_components.raw_data
        ]

        incident_components = []

        for comp in all_components:
            if comp.id in selected_components:
                incident_components.append(comp)

        incident = Incident(
            text=form.incident_text.data,
            impact=form.incident_impact.data,
            start_date=form.incident_start.data,
            components=incident_components,
        )
        db.session.add(incident)
        db.session.commit()
    return render_template(
        "create_incident.html", title="Open Incident", form=form
    )


@bp.route("/incidents/<incident_id>", methods=["GET"])
def incident(incident_id):
    """Get incident by ID"""
    incident = Incident.query.filter_by(id=incident_id).first_or_404()
    form = None
    if 'user' in session:
        form = IncidentUpdateForm(id)
    return render_template(
        "incident.html", title="Incident", incident=incident, form=form
    )


@bp.route("/incidents/<incident_id>/update", methods=["POST"])
@auth_required
def post_incident_update(incident_id):
    """Post update to the Incident"""
    form = IncidentUpdateForm(incident_id)
    if form.validate_on_submit():
        update = IncidentStatus(
            incident_id=incident_id,
            text=form.update_text.data,
            status=form.update_status.data,
        )
        db.session.add(update)
        db.session.commit()
    return redirect(url_for("web.incident", id=incident_id))


@bp.route("/login/<name>")
def login(name):
    """Login user using XXX auth method"""
    client = oauth.create_client(name)
    if not client:
        abort(404)

    redirect_uri = url_for("web.auth_callback", name=name, _external=True)
    return client.authorize_redirect(redirect_uri)


@bp.route("/auth/<name>")
def auth_callback(name):
    """Auth callback"""
    client = oauth.create_client(name)
    if not client:
        abort(404)

    token = client.authorize_access_token()
    current_app.logger.debug(token)
    user = token.get("userinfo")
    if not user:
        user = client.userinfo()

    current_app.logger.debug(user)

    required_group = current_app.config.get("OPENID_REQUIRED_GROUP")

    if required_group:
        if required_group not in user["groups"]:
            current_app.logger.info(
                "Not logging in user %s due to lack of required groups"
                % user.get("preferred_username", user.get("name"))
            )
            return redirect("/")

    session["user"] = user
    return redirect("/")


@bp.route("/logout")
def logout():
    """Logout user"""
    # remove the username from the session if it's there
    session.pop("user", None)
    return redirect("/")
