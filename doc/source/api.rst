===
API
===

Status Dashboard application comes with an API for opening incidents from
monitoring by posting component statuses.


Authorization for API requests
==============================

Authorizations for API requests based on the JWT usage
"SECRET_KEY" and "API_PAYLOAD_KEY" is defined in the app.config

Authorization will be passed If the "API_PAYLOAD_KEY" from the token's payload equals "API_PAYLOAD_KEY" from the app.config
and secret_key from the token equals "SECRET_KEY"

You should encode the "SECRET_KEY" to get the token
example:

.. code-block:: python3

>>> key = "dev"
>>> payload = {API_PAYLOAD_KEY: "some_value"}
>>> encoded = jwt.encode(payload, secret_key, algorithm="HS256")
>>> print(encoded)
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJwYXlsb2FkIjoiU09NRV9QQVlMT0FEIn0.oLj3UE3cQaviTpjOn0J6v0KE_wvPowyk2MAyN_s00_8


Get components
==============

Getting information about current components with assiciated incidents

.. code-block::

   curl http://localhost:5000/api/v1/component_status -X GET \
        -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'


Update component status
=======================

Push information from monitoring system about component status.

- when there is an active maintenance for the component no incident would be
  created

- when there is currently active maintenance not affecting the component incident
  might be created according to the following rules

- when there is current active incident for the component - no new incident
  will be opened

- when there is current active incident not affecting the component - given
  component will be added into the list of affected components of the incident

- when there is no active incident - a new incident will be opened

.. code-block:: console

   curl http://localhost:5000/api/v1/component_status -X POST \
        -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
        -H 'content-type:application/json' \
        -d '{"impact": "minor", "name": "Component 1", "attributes":[{"name":"region","value":"Reg1"}]}'
