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
    update_date = DateTimeField("Updated at:", format="%Y-%m-%dT%H:%M")
    timezone = StringField("Timezone", validators=[validators.DataRequired()])
    submit = SubmitField("Submit")

    def __init__(self, _start_date, _updates_ts, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # _start_date from the class Incident.start_date ()
        self._start_date = _start_date
        self._updates_ts = _updates_ts

    def validate_update_date(self, field):

        if field.data is None:
            if self.update_status.data in ["resolved", "reopened"]:
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
            "analyzing",
            "fixing",
            "observing",
            "impact changed",
            "resolved",
            "changed",
        ]:
            if upd_date_form > naive_utcnow():
                raise validators.ValidationError(
                    "The date cannot be in the future"
                )
            if upd_date_form < self._start_date:
                raise validators.ValidationError(
                    "The date cannot be before the start date"
                )
            for timestamp in self._updates_ts:
                if upd_date_form <= timestamp:
                    raise validators.ValidationError(
                        "The date cannot be before any "
                        "other status-update timestamp or equal"
                    )


class MaintenanceUpdateForm(FlaskForm):
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
    start_date = DateTimeField("Start date:", format="%Y-%m-%dT%H:%M")
    end_date = DateTimeField("End date:", format="%Y-%m-%dT%H:%M")
    update_date = DateTimeField("Updated at:", format="%Y-%m-%dT%H:%M")
    timezone = StringField("Timezone", validators=[validators.DataRequired()])
    submit = SubmitField("Submit")

    def __init__(self, _start_date, _end_date, _updates_ts, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._start_date = _start_date
        self._end_date = _end_date
        self._updates_ts = _updates_ts

    def validate_incident_start(self, field):
        start_date_form = naive_from_dttz(
            self.start_date.data,
            self.timezone.data,
        )
        if (
            self.incident_impact.data != "0"
            and start_date_form > naive_utcnow()
        ):
            raise validators.ValidationError(
                "Start date of incident cannot be in the future"
            )

    def validate_update_date(self, field):
        if field.data is None:
            if (
                self.update_status.data == "completed"
                and naive_utcnow() > self._start_date
            ):
                field.errors[:] = []
                raise validators.StopValidation()
            elif (
                self.update_status.data == "completed"
                and naive_utcnow() < self._start_date
            ):
                raise validators.ValidationError(
                    "Current time is earlier than maintenance start time.\n"
                    "You cannot complete an event that has not yet started."
                )
            elif self.update_status.data == "modified":
                field.errors[:] = []
                raise validators.StopValidation()
        if field.data is not None:
            upd_date_form = naive_from_dttz(
                self.update_date.data,
                self.timezone.data,
            )
            if (
                self.update_status.data == "completed"
                and upd_date_form < self._start_date
            ):
                raise validators.ValidationError(
                    "The date cannot be earlier than the start date"
                )
            elif (
                self.update_status.data == "completed"
                and naive_utcnow() < self._start_date
            ):
                raise validators.ValidationError(
                    "Current time is earlier than maintenance start time.\n"
                    "You cannot complete an event that has not yet started."
                )
            elif (
                self.update_status.data == "in progress"
                and upd_date_form > naive_utcnow()
            ):
                raise validators.ValidationError(
                    "Update date cannot be in the future"
                )
            elif self.update_status.data == "in progress" and self._updates_ts:
                raise validators.ValidationError(
                    "This maintenance already has a status update, "
                    "no statuses should be present."
                )
            elif (
                self.update_status.data == "in progress"
                and upd_date_form > self._end_date
            ):
                raise validators.ValidationError(
                    "Update date cannot be later than the end date"
                )

    def validate_start_date(self, field):
        if self.update_status.data != "modified":
            field.errors[:] = []
            raise validators.StopValidation()
        else:
            if field.data is None:
                raise validators.ValidationError("Start date cannot be empty")

            start_date_form = naive_from_dttz(
                field.data,
                self.timezone.data,
            )

            if self.end_date.data:
                end_date_form = naive_from_dttz(
                    self.end_date.data,
                    self.timezone.data,
                )
                if start_date_form > end_date_form:
                    raise validators.ValidationError(
                        "Start date cannot be later end date"
                    )
            for timestamp in self._updates_ts:
                if start_date_form > timestamp:
                    raise validators.ValidationError(
                        "Start date cannot be later any update timestamp"
                    )

    def validate_end_date(self, field):
        if self.update_status.data != "modified":
            field.errors[:] = []
            raise validators.StopValidation()
        else:
            if field.data is None:
                raise validators.ValidationError("End date cannot be empty")

            end_date_form = naive_from_dttz(
                field.data,
                self.timezone.data,
            )
            if self.start_date.data:
                start_date_form = naive_from_dttz(
                    self.start_date.data,
                    self.timezone.data,
                )
                if end_date_form < start_date_form:
                    raise validators.ValidationError(
                        "End date cannot be earlier than the start date"
                    )
            for timestamp in self._updates_ts:
                if end_date_form < timestamp:
                    raise validators.ValidationError(
                        "End date cannot be earlier than any update timestamp"
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
        "Start",
        validators=[validators.DataRequired()],
        format="%Y-%m-%dT%H:%M",
    )
    incident_end = DateTimeField(
        "End",
        validators=[validators.DataRequired()],
        format="%Y-%m-%dT%H:%M",
    )
    timezone = StringField("Timezone", validators=[validators.DataRequired()])

    submit = SubmitField("Submit")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.incident_impact.data == "0":
            self.incident_end.validators = [validators.DataRequired()]
        else:
            self.incident_end.validators = [validators.Optional()]

    def validate_incident_start(self, field):
        if not field.data:
            raise validators.ValidationError("Start date is required")

        start_date_form = naive_from_dttz(
            field.data,
            self.timezone.data,
        )

        if self.incident_impact.data and self.incident_impact.data != "0":
            if start_date_form > naive_utcnow():
                raise validators.ValidationError(
                    "Start date of incident cannot be in the future"
                )
        elif self.incident_impact.data == "0" and self.incident_end.data:
            # For maintenance, validate against end date
            end_date_form = naive_from_dttz(
                self.incident_end.data,
                self.timezone.data,
            )
            if start_date_form >= end_date_form:
                raise validators.ValidationError(
                    "Start date cannot be later than or equal to the end date"
                )
