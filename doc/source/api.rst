===
API
===

Status Dashboard application comes with an API for opening incidents from
monitoring by posting component statuses.

API is not designed to be used by humans using OpenID or oAuth. Therefore a
separate authorization is being used by the API.

Authorization for API requests
==============================

Authorizations for API
requests based on the JWT usage "SECRET_KEY" and "API_PAYLOAD_KEY" is
defined in the app.config.

Authorization will be passed If the "API_PAYLOAD_KEY" from the token's payload
equals "API_PAYLOAD_KEY" from the app.config and secret_key from the token
equals "SECRET_KEY"

You should encode the "SECRET_KEY" to get the token

.. code-block:: python

   >>> secret_key = "dev"
   >>> payload = {"status_dashboard": "dummy"}
   >>> encoded = jwt.encode(payload, secret_key, algorithm="HS256")
   >>> print(encoded)
   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJwYXlsb2FkIjoiU09NRV9Powyk2MN_s00_8

API usage examples
==================

.. code-block:: console

    $ curl http://localhost:5000/api/v1/component_status -X POST \
      -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6pX...' \
      -H 'content-type:application/json' \
      -d '{"impact": "minor", "name": "Component 1", \
      "attributes":[{"name":"region","value":"Reg1"}]}'

.. code-block:: console

    $ curl http://localhost:5000/api/v1/incidents -X GET \
      -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6Ikp...'

API v1
======

.. autoflask:: status_dashboard:app
   :blueprints: api
