====================
Prometheus exporter
====================

Status Dashboard application comes with a Prometheus exporter module

Description
===========

The exporter based on the "prometheus_client" library:

https://pypi.org/project/prometheus-client/

The exporter can be enabled or disabled using this variable:

app.config["PROMETHEUS_EXPORTER_ENABLED"] = True

The exporter collects metrics:

- request_count:

  - 'Total HTTP Requests'
  - ['method', 'endpoint', 'status']
- request_duration:

  - 'HTTP Request Duration'
  - ['method', 'endpoint', 'status']
- response_status_count:

  - 'HTTP Response Status Count'
- response_time_histogram:

  - 'HTTP Response Time in seconds'
- db_connection_gauge:
  - 'Database Connection Status (1 for connected, 0 for disconnected)'

metrics are available at the following endpoint:
http://127.0.0.1:5000/metrics
