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

from app import authorization
from app import cache
from app import oauth
from app.datetime import naive_from_dttz
from app.datetime import naive_utcnow
from app.models import Component
from app.models import ComponentAttribute
from app.models import Incident
from app.models import IncidentStatus
from app.models import db
from app.web import bp
from app.web.forms import IncidentForm
from app.web.forms import IncidentUpdateForm
from app.web.forms import MaintenanceUpdateForm

from dateutil.relativedelta import relativedelta

from flask import abort
from flask import current_app
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for


@bp.route("/", methods=["GET"])
@bp.route("/index", methods=["GET"])
@cache.cached(unless=lambda: "user" in session, key_prefix="/index")
def index():
    return render_template(
        "index.html",
        title="Status Dashboard",
        components=Component,
        component_attributes=ComponentAttribute,
        incidents=Incident,
        datetime_labels_script=True,
    )


def get_user_string(user):
    return f"{user['name']} ({user['email']})"


@authorization.auth_required
def update_incident(
    current_user,
    incident,
    text,
    status="SYSTEM",
    timestamp=None,
):
    if timestamp is None:
        timestamp = naive_utcnow()
    update = IncidentStatus(
        incident_id=incident.id,
        text=text,
        status=status,
        timestamp=timestamp,
    )
    db.session.add(update)
    current_app.logger.debug(
        f"Changes in {incident} by {get_user_string(current_user)}: {text}"
    )
    db.session.commit()


def form_submission(form, incident):
    new_impact = form.update_impact.data
    new_status = form.update_status.data
    update_date = (
        naive_from_dttz(
            form.update_date.data,
            form.timezone.data,
        )
        if form.update_date.data
        else None
    )

    redirect_path_map = {
        "completed": "/history",
        "resolved": "/history",
        "reopened": "/",
        "in progress": "/",
    }

    if new_status == "resolved":
        new_impact = incident.impact
        incident.end_date = update_date or naive_utcnow()
    elif new_status == "completed":
        new_impact = incident.impact
        update_date = naive_utcnow()
        incident.end_date = update_date
    elif new_status == "reopened":
        update_date = naive_utcnow()
        incident.end_date = None
    elif new_status == "changed":
        incident.end_date = update_date
        update_date = naive_utcnow()
    elif new_status == "in progress":
        incident.start_date = update_date
        update_date = naive_utcnow()
    elif new_status == "modified":
        if form.start_date.data:
            incident.start_date = naive_from_dttz(
                form.start_date.data,
                form.timezone.data,
            )
        if form.end_date.data:
            incident.end_date = naive_from_dttz(
                form.end_date.data,
                form.timezone.data,
            )
        update_date = naive_utcnow()
    elif new_status in [
        "analyzing",
        "fixing",
        "observing",
    ]:
        new_impact = incident.impact

    redirect_path = redirect_path_map.get(
        new_status,
        f"/incidents/{incident.id}",
    )

    if new_status in [
        "completed",
        "resolved",
        "reopened",
        "changed",
        "in progress",
        "modified",
    ]:
        log_message = (
            f"{incident} '{new_status}' by {get_user_string(session['user'])}"
        )
        if new_status == "in progress":
            log_message += f", start date is set: {incident.start_date}"
        current_app.logger.debug(log_message)

    incident.text = form.update_title.data
    incident.impact = new_impact
    incident.system = False
    update_incident(incident, form.update_text.data, new_status, update_date)

    return redirect_path


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

    active_incidents = Incident.get_all_active()

    if form.validate_on_submit():
        selected_components = [
            int(x) for x in form.incident_components.raw_data
        ]

        incident_components = [
            comp for comp in all_components if comp.id in selected_components
        ]
        new_incident = Incident(
            text=form.incident_text.data,
            impact=form.incident_impact.data,
            start_date=naive_from_dttz(
                form.incident_start.data,
                form.timezone.data,
            ),
            components=incident_components,
            system=False,
        )

        if form.incident_impact.data == "0":
            new_incident.end_date = naive_from_dttz(
                form.incident_end.data,
                form.timezone.data,
            )

        db.session.add(new_incident)
        db.session.commit()

        if form.incident_impact.data == "0" and form.incident_desc.data:
            add_desc = IncidentStatus(
                incident_id=new_incident.id,
                text=form.incident_desc.data,
                status="description",
            )
            db.session.add(add_desc)
            db.session.commit()

        current_app.logger.debug(
            f"{new_incident} opened by {get_user_string(current_user)}"
        )

        if form.incident_impact.data != "0":
            messages_from = []

            for inc in active_incidents:
                messages_to = []
                for comp in incident_components:
                    if comp in inc.components:
                        comp_name = comp.name
                        comp_attributes = comp.attributes
                        comp_attributes_str = ", ".join(
                            [f"{attr.value}" for attr in comp_attributes]
                        )
                        comp_with_attrs = (
                            f"{comp_name} " f"({comp_attributes_str})"
                        )
                        url_s = url_for("web.incident", incident_id=inc.id)
                        link_s = f"<a href='{url_s}'>{inc.text}</a>"
                        url_d = url_for(
                            "web.incident", incident_id=new_incident.id
                        )
                        link_d = f"<a href='{url_d}'>{new_incident.text}</a>"
                        update_s = f"{comp_with_attrs} moved to {link_d}"
                        update_n = f"{comp_with_attrs} moved from {link_s}"
                        messages_to.append(update_s)
                        messages_from.append(update_n)

                        if len(inc.components) > 1:
                            inc.components.remove(comp)
                        else:
                            messages_to.append("Incident closed by system")
                            inc.end_date = naive_utcnow()
                if messages_to:
                    update_incident(inc, ", ".join(messages_to))
            if messages_from:
                update_incident(new_incident, ", ".join(messages_from))
        db.session.commit()

        return (
            redirect("/")
            if new_incident.impact != 0
            else redirect("/incidents/" + str(new_incident.id))
        )

    return render_template(
        "create_incident.html",
        title="Open Incident",
        form=form,
    )


@bp.route("/incidents/<incident_id>", methods=["GET", "POST"])
@cache.cached(
    unless=lambda: "user" in session,
    key_prefix=lambda: f"{request.path}",
)
def incident(incident_id):
    """Manage incident by ID"""
    incident = Incident.get_by_id(incident_id)
    if not incident:
        abort(404)

    form = None
    start_date = incident.start_date
    if incident.end_date:
        end_date = incident.end_date
    else:
        end_date = None
    updates = incident.updates
    updates_ts = [
        u.timestamp
        for u in updates
        if u.status
        not in [
            "resolved",
            "description",
            "changed",
            "modified",
        ]
    ]
    now = naive_utcnow()

    if "user" in session:

        if incident.impact == 0:
            form = MaintenanceUpdateForm(start_date, end_date, updates_ts)
        else:
            form = IncidentUpdateForm(start_date, updates_ts)
        # update_impact will contain choices based on the incident_type
        choices = [
            (v.value, v.string)
            for (_, v) in current_app.config["INCIDENT_IMPACTS"].items()
            if (
                (incident.impact == 0 and v.value == 0)
                or (incident.impact != 0 and v.value != 0)
            )
        ]

        form.update_impact.choices = choices
        # Update_status will contain choices based on the incident_type
        form.update_status.choices = [
            (k, v)
            for (k, v) in current_app.config.get(
                (
                    "INCIDENT_ACTIONS"
                    if incident.end_date and incident.impact != 0
                    else (
                        "MAINTENANCE_STATUSES"
                        if incident.impact == 0
                        else "INCIDENT_STATUSES"
                    )
                ),
                {},
            ).items()
        ]

        if form.validate_on_submit():
            redirect_path = form_submission(form, incident)
            return redirect(redirect_path)

    return render_template(
        "incident.html",
        title="Incident",
        incident=incident,
        form=form,
        now=now,
        incident_datelabels_script=True,
        datetime_labels_script=True,
    )


@bp.route("/separate/<incident_id>/<component_id>")
@authorization.auth_required
def separate_incident(current_user, incident_id, component_id):
    """Separate a component into a new incident"""
    component = Component.get_by_id(component_id)
    incident = Incident.get_by_id(incident_id)
    incident.components.remove(component)

    new_incident = Incident(
        text=f"{incident.text} ({component.name})",
        impact=incident.impact,
        start_date=incident.start_date,
        components=[component],
        system=False,
    )
    db.session.add(new_incident)
    db.session.commit()

    current_app.logger.debug(
        f"{new_incident} opened by {get_user_string(current_user)}"
    )

    comp_name = component.name
    comp_attributes = component.attributes
    comp_attributes_str = ", ".join(
        [f"{attr.value}" for attr in comp_attributes]
    )
    comp_with_attrs = f"{comp_name} ({comp_attributes_str})"

    url_s = url_for("web.incident", incident_id=incident.id)
    link_s = f"<a href='{url_s}'>{incident.text}</a>"
    url_d = url_for("web.incident", incident_id=new_incident.id)
    link_d = f"<a href='{url_d}'>{new_incident.text}</a>"

    update_s = f"{comp_with_attrs} moved to {link_d}"
    update_n = f"{comp_with_attrs} moved from {link_s}"

    update_incident(incident, update_s)
    update_incident(new_incident, update_n)
    db.session.commit()
    return redirect("/")


@bp.route("/history", methods=["GET"])
@cache.cached(unless=lambda: "user" in session)
def history():
    return render_template(
        "history.html",
        title="Event History",
        incidents=Incident,
        datetime_labels_script=True,
    )


@bp.route("/availability", methods=["GET"])
@cache.cached(
    unless=lambda: "user" in session,
    timeout=300,
)
def sla():
    time_now = naive_utcnow()
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
