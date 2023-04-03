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
import os
import pathlib

from app.default_settings import DefaultConfiguration

from authlib.integrations.flask_client import OAuth

from flask import Flask

from flask_caching import Cache

from flask_migrate import Migrate

from flask_smorest import Api

from flask_sqlalchemy import SQLAlchemy

import yaml


db = SQLAlchemy()
migrate = Migrate()
oauth = OAuth()
cache = Cache(config={"CACHE_TYPE": "SimpleCache"})


def create_app(test_config=None):
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(DefaultConfiguration)

    api = Api(app) # noqa

    app.config.from_prefixed_env(prefix="SDB")

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile("config.py", silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    if (
        "SQLALCHEMY_DATABASE_URI" not in app.config
        and "DATABASE_URI" in app.config
    ):
        app.config["SQLALCHEMY_DATABASE_URI"] = app.config["DATABASE_URI"]
    if "SQLALCHEMY_DATABASE_URI" not in app.config:
        # TODO(gtema): sooner or later this should be dropped
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///example.sqlite"

    config_file = pathlib.Path(app.instance_path, 'catalog.yaml')
    if config_file.exists():
        with open(config_file, 'r') as fd:
            app.config['CATALOG'] = yaml.safe_load(fd)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    cache.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    oauth.init_app(app, cache=cache)

    if (
        "GITHUB_CLIENT_ID" in app.config
        and "GITHUB_CLIENT_SECRET" in app.config
    ):
        app.logger.debug("Enabling GitHub auth")
        oauth.register(
            name="github",
            client_id=app.config["GITHUB_CLIENT_ID"],
            client_secret=app.config["GITHUB_CLIENT_SECRET"],
            access_token_url="https://github.com/login/oauth/access_token",
            access_token_params=None,
            authorize_url="https://github.com/login/oauth/authorize",
            authorize_params=None,
            api_base_url="https://api.github.com/",
            client_kwargs={"scope": "user"},
            userinfo_endpoint="https://api.github.com/user",
        )
    if (
        "OPENID_ISSUER_URL" in app.config
        and "OPENID_CLIENT_ID" in app.config
        and "OPENID_CLIENT_SECRET" in app.config
    ):
        app.logger.debug("Enabling OpenID auth")
        metadata_url = (
            f"{app.config['OPENID_ISSUER_URL']}"
            "/.well-known/openid-configuration"
        )
        oauth.register(
            name="openid",
            client_id=app.config["OPENID_CLIENT_ID"],
            client_secret=app.config["OPENID_CLIENT_SECRET"],
            server_metadata_url=metadata_url,
            # client_kwargs={"scope": "openid profile status-dashboard-aud"},
            client_kwargs={"scope": "openid profile"},
            token_placement="header",
        )

    from app.web import bp as web_bp
    from app.api import bp as api_bp

    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    with app.app_context():
        # Ensure there is some DB when we start the app
        db.create_all()

    return app
