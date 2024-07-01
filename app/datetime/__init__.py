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
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo


def datetime_utcnow():
    # type: () -> datetime
    return datetime.now(timezone.utc)


def utc_from_timestamp(timestamp):
    # type: (float) -> datetime
    return datetime.fromtimestamp(timestamp, timezone.utc)

def naive_from_timestamp(timestamp):
    return utc_from_timestamp(timestamp).replace(tzinfo=None)

def naive_utcnow():
    return datetime_utcnow().replace(tzinfo=None)

def naive_from_dttz(timeobject: datetime, timezone: str) -> datetime:
    if timeobject is None:
        raise ValueError("timeobject cannot be None")
    if timezone is None:
        raise ValueError("timezone cannot be None")
    try:
        tz = ZoneInfo(timezone)
    except Exception as e:
        raise ValueError(f"Invalid timezone: {timezone}") from e
    date_new_tz = timeobject.replace(tzinfo=tz)
    return naive_from_timestamp(date_new_tz.timestamp())
