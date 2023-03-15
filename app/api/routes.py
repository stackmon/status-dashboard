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

from .resources import incidents, components


def initialize_routes(api):
    api.add_resource(incidents.ApiIncidents, '/api/v1/incidents')
    api.add_resource(incidents.ApiIncident, "/api/v1/incidents/<int:incident_id>")
    api.add_resource(components.ApiInfo, "/api/v1/info")
    api.add_resource(components.ApiComponents, "/api/v1/components")
    api.add_resource(components.UniqueComponents, "/api/v1/unique_components")
