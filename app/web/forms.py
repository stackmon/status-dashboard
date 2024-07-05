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
from app.datetime import naive_from_dttz
from app.datetime import naive_utcnow

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
    update_date = DateTimeField("Next Update by", format='%Y-%m-%dT%H:%M')
    timezone = StringField("Timezone", validators=[validators.DataRequired()])
    submit = SubmitField("Submit")

    def __init__(self, _start_date, _updates_ts, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # _start_date from the class Incident.start_date ()
        self._start_date = _start_date
        self._updates_ts = _updates_ts

    def validate_update_date(self, field):

        if field.data is None:
            if self.update_status.data in [
                "resolved",
                "completed",
                "reopened"
            ]:
                field.errors[:] = []
                raise validators.StopValidation()
            elif self.update_status.data == "changed":
                raise validators.ValidationError(
                    "New end date field cannot be empty"
                )

        if field.data is not None:
            upd_date_form = naive_from_dttz(
                self.update_date.data,
                self.timezone.data,
            )
        else:
            upd_date_form = None
            raise validators.ValidationError("Update date cannot be empty")

        if self.update_status.data in [
            "resolved",
            "completed",
            "reopened",
        ]:
            if upd_date_form > naive_utcnow():
                raise validators.ValidationError(
                    "End date cannot be in the future"
                )
            if upd_date_form < self._start_date:
                raise validators.ValidationError(
                    "End date cannot be before the start date"
                )
            if field.data is not None and field.data < self._start_date:
                raise validators.ValidationError(
                    "End date cannot be before the start date"
                )
            for timestamp in self._updates_ts:
                if upd_date_form <= timestamp:
                    raise validators.ValidationError(
                        "End date cannot be before any "
                        "other status-update timestamp or equal"
                    )
        elif self.update_status.data == "changed":
            if upd_date_form > naive_utcnow():
                raise validators.ValidationError(
                    "End date cannot be in the future"
                )
            if upd_date_form < self._start_date:
                raise validators.ValidationError(
                    "End date cannot be before the start date"
                )
            if field.data < self._start_date:
                raise validators.ValidationError(
                    "End date cannot be before the start date"
                )
            for timestamp in self._updates_ts:
                if upd_date_form <= timestamp:
                    raise validators.ValidationError(
                        "End date cannot be before any "
                        "other status-update timestamp or equal"
                    )
        elif self.update_status.data in [
            "analyzing",
            "fixing",
            "observing",
            "in progress"
        ]:
            if upd_date_form > naive_utcnow():
                raise validators.ValidationError(
                    "Update date cannot be in the future"
                )
            if upd_date_form < self._start_date:
                raise validators.ValidationError(
                    "End date cannot be before the start date"
                )
            for timestamp in self._updates_ts:
                if upd_date_form <= timestamp:
                    raise validators.ValidationError(
                        "End date cannot be before any "
                        "other status-update timestamp or equal"
                    )
        if self.update_status.data == "scheduled":
            if upd_date_form < self._start_date:
                raise validators.ValidationError(
                    "Scheduled date cannot be before the start date"
                )
            for timestamp in self._updates_ts:
                if upd_date_form <= timestamp:
                    raise validators.ValidationError(
                        "Scheduled date cannot be before any "
                        "other status-update timestamp or equal"
                    )


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
    timezone = StringField("Timezone", validators=[validators.DataRequired()])

    submit = SubmitField("Submit")

    def validate_incident_start(self, field):
        start_date_form = naive_from_dttz(
            self.incident_start.data,
            self.timezone.data,
        )
        if (
            self.incident_impact.data != "0"
            and start_date_form > naive_utcnow()
        ):
            raise validators.ValidationError(
                "Start date of incident cannot be in the future"
            )

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
