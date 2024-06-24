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


class Impact:
    def __init__(self, value, key, string):
        self.value = value
        self.key = key
        self.string = string


class DefaultConfiguration:
    API_TITLE = "Status Dashboard API"
    API_VERSION = "v1"
    API_PAYLOAD_KEY = "stackmon"
    OPENAPI_VERSION = "3.1.0"
    OPENAPI_URL_PREFIX = "/"
    OPENAPI_JSON_PATH = "api-spec.json"
    SECRET_KEY = "dev"
    SQLALCHEMY_ECHO = False
    JSON_SORT_KEYS = True
    # cache settings
    CACHE_KEY_PREFIX = "sdb_cache:"
    CACHE_DEFAULT_TIMEOUT = 30
    CACHE_TYPE = "SimpleCache"

    # Incident impacts map
    # key - integer to identify impact and compare "severity"
    # value - tuple of
    #    - impact alias - used in the css
    #    - string description of the impact
    # NOTE: Maintenance must have key 0
    INCIDENT_IMPACTS = {
        0: Impact(0, "maintenance", "Scheduled maintenance"),
        1: Impact(1, "minor", "Minor incident (i.e. performance impact)"),
        2: Impact(2, "major", "Major incident"),
        3: Impact(3, "outage", "Service outage"),
    }

    MAINTENANCE_STATUSES = {
        "scheduled": "Maintenance scheduled",
        "in progress": "Maintenance is in progress",
        "completed": "Maintenance is successfully completed",
    }

    INCIDENT_STATUSES = {
        "analyzing": "Analyzing incident (problem not known yet)",
        "fixing": "Fixing incident (problem identified, working on fix)",
        "observing": "Observing fix (fix deployed, watching recovery)",
        "resolved": "Incident Resolved (service is fully available. Done)",
    }

    INCIDENT_ACTIONS = {
        "reopened" : "Incident reopened (resolved incident has ben reopened)",
        "changed" : "Incident changed: (resolved incident has been changed)",
    }
