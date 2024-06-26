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

from flask_wtf import FlaskForm

from wtforms import DateTimeField
from wtforms import SelectField
from wtforms import StringField
from wtforms import SubmitField
from wtforms import TextAreaField
from wtforms import validators


class IncidentUpdateForm(FlaskForm):
    update_title = StringField(
        "Incident Title",
        validators=[
            validators.DataRequired(),
            validators.Length(min=8, max=200),
        ],
    )
    update_text = TextAreaField(
        "Update Message",
        validators=[
            validators.DataRequired(),
            validators.Length(min=10, max=200),
        ],
    )
    update_impact = SelectField("Incident Impact")
    update_status = SelectField("Update Status")
    next_update = DateTimeField("Next Update by", format='%Y-%m-%dT%H:%M')
    submit = SubmitField("Submit")

    def __init__(self, incident_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.incident_id = incident_id

    def validate_next_update(self, field):
        if (
            self.update_status.data not in ["resolved", "completed"]
            and field.data is None
        ):
            raise validators.ValidationError(
                "Next update field is mandatory unless " "incident is resolved"
            )
        elif (
            self.update_status.data in ["resolved", "completed"]
            and field.data is None
        ):
            # Making field optional requres dropping "Not a valid datetime
            # value." error as well
            field.errors[:] = []
            raise validators.StopValidation()


class IncidentForm(FlaskForm):
    incident_text = StringField(
        "Incident Title",
        validators=[
            validators.DataRequired(),
            validators.Length(min=8, max=200),
        ],
    )
    incident_desc = TextAreaField(
        "Maintenance Description",
        validators=[
            validators.Optional(),
            validators.Length(min=8, max=500),
        ],
    )
    incident_impact = SelectField("Incident Impact")
    incident_components = SelectField("Affected services")
    incident_start = DateTimeField(
        "Start", validators=[validators.DataRequired()],
        format='%Y-%m-%dT%H:%M'
    )
    incident_end = DateTimeField(
        "End", format='%Y-%m-%dT%H:%M'
    )
    incident_start_utc = DateTimeField("Start UTC")
    incident_end_utc = DateTimeField("End UTC")
    submit = SubmitField("Submit")

    def validate_incident_end(self, field):
        if (
            self.incident_impact.data == "0"
            and field.data is None
        ):
            raise validators.ValidationError(
                "Expected end date field is mandatory for maintenance"
            )
        elif (
            self.incident_impact.data != "0"
            and field.data is None
        ):
            # Making field optional requres dropping "Not a valid datetime
            # value." error as well
            field.errors[:] = []
            raise validators.StopValidation()

    def validate_incident_end_utc(self, field):
        if (
            self.incident_impact.data == "0"
            and field.data is None
        ):
            raise validators.ValidationError(
                "Expected end date field is mandatory for maintenance"
            )
        elif (
            self.incident_impact.data != "0"
            and field.data is None
        ):
            field.errors[:] = []
            raise validators.StopValidation()
