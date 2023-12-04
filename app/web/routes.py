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

from app import authorization
from app import oauth
from app.models import Component
from app.models import ComponentAttribute
from app.models import Incident
from app.models import IncidentStatus
from app.models import db
from app.web import bp
from app.web.forms import IncidentForm
from app.web.forms import IncidentUpdateForm

from dateutil.relativedelta import relativedelta

from flask import abort
from flask import current_app
from flask import flash
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
@authorization.auth_required
def new_incident(current_user):
    """Create new Incident"""
    all_components = Component.all()
    form = IncidentForm()
    form.incident_components.choices = [(c.id, c) for c in all_components]
    form.incident_impact.choices = [
        (v.value, v.string)
        for (_, v) in current_app.config["INCIDENT_IMPACTS"].items()
    ]

    if form.validate_on_submit():
        selected_components = [
            int(x) for x in form.incident_components.raw_data
        ]

        incident_components = []

        for comp in all_components:
            if comp.id in selected_components:
                incident_components.append(comp)

        new_incident = Incident(
            text=form.incident_text.data,
            impact=form.incident_impact.data,
            start_date=form.incident_start.data,
            components=incident_components,
        )
        db.session.add(new_incident)
        db.session.commit()
        return redirect("/")
    return render_template(
        "create_incident.html", title="Open Incident", form=form
    )


@bp.route("/incidents/<incident_id>", methods=["GET", "POST"])
def incident(incident_id):
    """Manage incident by ID"""
    incident = Incident.get_by_id(incident_id)
    form = None
    if "user" in session:
        form = IncidentUpdateForm(id)
        # Update_status will contain choices based on the incident_type
        form.update_status.choices = [
            (k, v)
            for (k, v) in current_app.config.get(
                "MAINTENANCE_STATUSES"
                if incident.impact == 0
                else "INCIDENT_STATUSES",
                {},
            ).items()
        ]

        if form.validate_on_submit():
            new_status = form.update_status.data
            update = IncidentStatus(
                incident_id=incident_id,
                text=form.update_text.data,
                status=new_status,
            )
            db.session.add(update)
            if new_status in ["completed", "resolved"]:
                # Incident is completed
                incident.end_date = datetime.now()
            incident.text = form.update_title.data
            db.session.commit()

    return render_template(
        "incident.html", title="Incident", incident=incident, form=form
    )


@bp.route("/history", methods=["GET"])
def history():
    return render_template(
        "history.html",
        title="Incident History",
        incidents=Incident,
    )


@bp.route("/availability", methods=["GET"])
def sla():
    time_now = datetime.now()
    months = [time_now + relativedelta(months=-mon) for mon in range(6)]

    return render_template(
        "sla.html",
        title="Component Availability",
        components=Component,
        component_attributes=ComponentAttribute,
        incidents=Incident,
        months=months,
    )


@bp.route("/login/<name>")
def login(name):
    """Login

    Initialize user login process with chosen auth method

    :param str auth: One of ['github', 'openid']
    """
    client = oauth.create_client(name)
    if not client:
        abort(404)

    redirect_uri = url_for("web.auth_callback", name=name, _external=True)
    return client.authorize_redirect(redirect_uri)


@bp.route("/auth/<name>")
def auth_callback(name):
    """Auth callback

    Callback invoked by the auth provider

    :param str auth: One of ['github', 'openid']
    """
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
            flash(
                "Not logging in user %s due to lack of required groups"
                % user.get("preferred_username", user.get("name"))
            )
            return redirect("/")

    session["user"] = user
    return redirect("/")


@bp.route("/logout")
def logout():
    """Logout

    Logout user
    """
    # remove the username from the session if it's there
    session.pop("user", None)
    return redirect("/")
