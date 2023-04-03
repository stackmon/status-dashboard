===
API
===

Status Dashboard application comes with an API for opening incidents from
monitoring by posting component statuses.

Get components
==============

Getting information about current components with assiciated incidents

.. code-block::

   curl http://localhost:5000/api/v1/component_status -X GET


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

   curl http://localhost:5000/api/v1/component_status X POST -H 'content-type:application/json' -d '{"impact": "minor", "name": "Component 1", "attributes":[{"name":"region","value":"Reg1"}]}'
