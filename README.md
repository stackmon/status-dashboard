# Status Dashboard

## Trying it out

```
tox -e py39
source .tox/py39/bin/activate
export FLASK_APP=status_dashboard.py
flask db upgrade  # Initialize DB
flask --debug run

flask db stamp head # to start the upgrade db models
```
### Redis
It needs to run with redis;  
Environment variables can be configured using the "SDB" prefix.
```
"SDB_CACHE_TYPE"
"SDB_CACHE_KEY_PREFIX"
"SDB_CACHE_REDIS_HOST"
"SDB_CACHE_REDIS_PORT"
"SDB_CACHE_REDIS_URL"
"SDB_CACHE_REDIS_PASSWORD"
"SDB_CACHE_DEFAULT_TIMEOUT"
```

## Bootstraping

It is possible to bootstrap DB with some initial data.  
To create and purge the test data run the command:
```
flask bootstrap provision
flask bootstrap purge
```

## Architecture

As stupidly simple as possible:

- flask to impement "API" and render web
- web pages without JavaScript logic (kiss and working with JS blockers)
- DB (using through sqlalchemy)
- bootstrap
- auth to be done with OpenID connect
- services are representing what should be verified (working or not)
- service_category - meta grouping of services into groups
- regions - different services are existing in regions (many to many relation)
- incidents - entry about issues affecting certain regions and certain services
- incident_status - change history (or incident updates)


Initial sketch diagram (no 100% matching reality)

```mermaid
classDiagram

    class Incident{
      -int id
      +date start
      +date end
      +string text
      +enum impact [maintenance, minor, major, outage]
      -int user_id

      +get_incidents(start, end, impact)
    }

    class IncidentStatuses{
        -int incident_id
        +date time
        +enum status [scheduled, investigating, identified, watching, fixed]
        +string text
        -int user_id

        get_incident_statuses(incident_id)
    }

    class IncidentServiceRelation{
        -int incident_id
        -int service_id
    }

    class IncidentRegionRelation {
        -int incident_id
        -int region_id
    }

    class Service {
      -int id
      +string name
      +string category
    }

    class Region{
        -int id
        +string name
    }

    class Operator {
        -int user_id
        
    }
```

A real data model is however represented in https://github.com/stackmon/status-dashboard/blob/main/app/models.py

# Developing

Flask requires environment variable `FLASK_APP` to be set to
`status-dashboard.py` or this variable can be passed to every flask command
invocation.

## Environment

In a regular case it is recommended to rely on tox for managing all virtual environments.

`tox -e py3 --notest` will create new python virtual environment and install
all project dependencies.

Once environment is prepared it is required to source into it `source
.tox/py3/bin/activate` before doing any further steps.

## DB

For the development builtin sqlite database is absolutely sufficient.

`flask db upgrade` command with install default DB schema.

## Data

Test catalog data is placed in the `app/tests/config/catalog.yaml`. This file
should be copied into the instance directory (`cwd/instance`) and command
`flask bootstrap provision` should be executed. 
