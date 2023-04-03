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
from functools import wraps

from app.default_settings import DefaultConfiguration

from flask_httpauth import HTTPTokenAuth

import jwt


class ApiHTTPTokenAuth(HTTPTokenAuth):
    def login_required(self, func):
        auth_required_func = super().login_required(func)

        @wraps(func)
        def wrapper(*args, **kwargs):
            return auth_required_func(*args, **kwargs)

        params = {
            "name": "Authorization",
            "in": "header",
            "description": "Authorization: Bearer <access_token>",
            "required": "true",
        }

        wrapper._apidoc = getattr(func, "_apidoc", {})
        wrapper._apidoc.setdefault("params", []).append(params)

        return wrapper


auth = ApiHTTPTokenAuth(scheme="Bearer")

secret_key = DefaultConfiguration.SECRET_KEY
users = ["stackmon",]
for user in users:
    token = jwt.encode(
        {"username": user},
        secret_key,
        algorithm="HS256"
    )
    print("*** token for {}: {}\n".format(user, token))


@auth.verify_token
def verify_token(token):
    try:
        data = jwt.decode(token, secret_key,
                          algorithms=["HS256"])
    except:     # noqa:E722
        return False
    if "username" in data:
        return data["username"]
