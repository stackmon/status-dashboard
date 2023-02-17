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

# from flask import request
from flask_wtf import FlaskForm
from wtforms import SubmitField
from wtforms import TextAreaField
from wtforms import SelectField
from wtforms import DateTimeField
# from wtforms.validators import ValidationError
from wtforms.validators import DataRequired
from wtforms.validators import Length
# from wtforms.validators import AnyOf
# from app.models import IncidentStatus


class IncidentUpdateForm(FlaskForm):
    update_text = TextAreaField(
        "Update Message", validators=[DataRequired(), Length(min=10, max=200)]
    )
    update_status = SelectField(
        "Update Status",
        choices=[
            ("scheduled", "Maintenance scheduled"),
            ("in progress", "Maintenance is in progress"),
            ("completed", "Maintenance is successfully completed"),
            ("analyzing", "Analyzing incident (problem not known yet"),
            ("fixing", "Fixing incident(problem identified, working on fix)"),
            ("observing", "Observing fix (fix deployed, watching recovery)"),
            (
                "resolved",
                "Incident Resolved (service is fully available. Done)",
            ),
        ],
    )
    next_update = DateTimeField("Next Update by", validators=[DataRequired()])
    submit = SubmitField("Submit")

    def __init__(self, incident_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.incident_id = incident_id


class IncidentForm(FlaskForm):
    incident_text = TextAreaField(
        "Incident summary", validators=[
            DataRequired(),
            Length(min=10, max=200)]
    )
    incident_impact = SelectField(
        "Incident Impact",
        choices=[
            ("maintenance", "Scheduled maintenance"),
            ("minor", "Minor incident (i.e. performance impact)"),
            ("major", "Major incident"),
            ("outage", "Service outage"),
        ]
    )
    incident_regions = SelectField(
        "Affected Regions"
    )
    incident_services = SelectField(
        "Affected services"
    )
    incident_start = DateTimeField("Start", validators=[DataRequired()])
    submit = SubmitField("Submit")
