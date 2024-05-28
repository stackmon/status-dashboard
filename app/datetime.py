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
from datetime import datetime, timezone


def datetime_utcnow():
    # type: () -> datetime
    return datetime.now(timezone.utc)


def utc_from_timestamp(timestamp):
    # type: (float) -> datetime
    return datetime.fromtimestamp(timestamp, timezone.utc)


def naive_utcnow():
    return datetime_utcnow().replace(tzinfo=None)
