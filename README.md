# Status Dashboard

## Trying it out

```
tox -e py39
source .tox/py39/bin/activate
flask A status_dashboard.py --debug run
```

## Bootstraping

It is possible to bootstrap DB with some initial data

```
flask boostrap provision
```

## DB Architecture

```mermaid
classDiagram
   Incident "1" -- "*" IncidentStatuses
   Incident "1" -- "*" IncidentServiceRelation
   Incident "1" -- "*" IncidentRegionRelation
   Service "1" -- "*" IncidentServiceRelation
   Region "1" -- "*" IncidentRegionRelation
   Operator "1" -- "*" Incident
   Operator "1" -- "*" IncidentStatuses

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

