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

from flask import render_template
# from flask import flash
from flask import redirect
from flask import url_for
# from flask import request
# from flask import g
# from flask import jsonify
# from flask import current_app

from app import db

from app.models import Region
from app.models import Incident
from app.models import IncidentStatus
from app.models import Service
from app.models import ServiceCategory


from app.web import bp
from app.web.forms import IncidentForm
from app.web.forms import IncidentUpdateForm


@bp.route("/", methods=["GET", "POST"])
@bp.route("/index", methods=["GET", "POST"])
def index():
    categories = ServiceCategory.query.all()
    regions = Region.query.all()
    incidents = Incident.open()
    return render_template(
        "index.html",
        title="Home",
        regions=regions,
        categories=categories,
        incidents=incidents,
    )


@bp.route("/incidents", methods=["GET", "POST"])
def new_incident():
    all_regions = Region.query.order_by(Region.name).all()
    all_services = Service.query.order_by(Service.name).all()
    form = IncidentForm()
    form.incident_services.choices = [
        (s.id, s.name) for s in all_services
    ]
    form.incident_regions.choices = [
        (s.id, s.name) for s in all_regions
    ]
    if form.validate_on_submit():
        selected_regions = [int(x) for x in form.incident_regions.raw_data]
        selected_services = [int(x) for x in form.incident_services.raw_data]
        incident_regions = []
        incident_services = []
        for reg in all_regions:
            if reg.id in selected_regions:
                incident_regions.append(reg)
        for srv in all_services:
            if srv.id in selected_services:
                incident_services.append(srv)

        incident = Incident(
            text=form.incident_text.data,
            impact=form.incident_impact.data,
            start_date=form.incident_start.data,
            regions=incident_regions,
            services=incident_services
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
