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

from marshmallow import Schema, fields, validate


class ComponentSearchQueryArgs(Schema):
    name = fields.String()
    attribute_name = fields.String()
    attribute_value = fields.String()


class ComponentAttributeSchema(Schema):
    name = fields.String(required=True)
    value = fields.String(required=True)


class IncidentSchema(Schema):
    id = fields.Integer(dump_only=True)
    text = fields.String(required=True)
    impact = fields.String(required=True)
    start_date = fields.Date(required=True)
    end_date = fields.Date()


class ComponentSchema(Schema):
    id = fields.Integer(dump_only=True)
    name = fields.String(required=True)
    attributes = fields.List(fields.Nested(ComponentAttributeSchema))
    incidents = fields.List(fields.Nested(IncidentSchema))


class ComponentStatusArgsSchema(Schema):
    impact = fields.String(
        required=True,
        validate=validate.OneOf(["maintenance", "minor", "major", "outage"]),
    )
    name = fields.String(required=True)
    attributes = fields.List(fields.Nested(ComponentAttributeSchema))
