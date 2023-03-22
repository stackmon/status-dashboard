=============
Configuration
=============

StatusDashboard can be configured through the environment variables.

* `SDB_SECRET_KEY` - Secret Key of the Flask application used for encryption

* `SDB_SQLALCHEMY_DATABASE_URI`/`SDB_DATABASE_URI` - database URI

* `SDB_GITHUB_CLIENT_ID`

* `SDB_GITHUB_CLIENT_SECRET`

* `SDB_OPENID_ISSUER_URL`

* `SDB_OPENID_CLIENT_ID`

* `SDB_OPENID_CLIENT_SECRET`

* `SDB_OPENID_REQUIRED_GROUP`


Components configuration
========================

It is possible to define required components with theirattributes in a yaml
file and bootstrap this data into the database using the CLI. This requires
placing file named like `catalog.yaml` into the instance folder (normally
`cwd/instance` ) with the content in the following form:

.. code-block:: yaml

   components:
     - name: Component11
       attributes:
         attr1: val1
         attr2: val2
     - name: Component12
       attributes:
         attr1: val1
         attr2: val2
     - name: Component13
       attributes:
         attr1: val1
         attr2: val2

Status Dashboard flask app provides few cli command

`flask bootstrap purge` - lets clean all database entries

`flask bootstrap provision` - Inserts components configuration into the
database as defined by the `catalog.yaml` file. During that no existing entries
are deleted by default, and instead presence of the configured entries is
ensured.
