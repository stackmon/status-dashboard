==========================================
Websocket Server for the Status Dashboard
==========================================
The Status Dashboard application includes a WebSocket server module that
provides real-time updates about incidents to connected clients.
Status Dashboard application comes with a WebSocket server based onasync
approach. WebSocket Server created to receive incident changes and send
them to the clients when clients are connected to the server.

==============================

Description:
============
The WebSocket server module utilizes the "aiohttp" library for handling
WebSocket connections and communicating with the API of the Status Dashboard
to fetch incident data. It also relies on the "websockets" library to serve
the WebSocket connections. The server is implemented as a separate component
and runs in a separate container from the status dashboard.

The module performs the following main tasks:

1. Handling WebSocket Connections: The WebSocket server accepts incoming
   connections from clients and maintains a set of connected clients.

2. Fetching Data from API: The module periodically fetches incident data from
   the API of the Status Dashboard. The frequency of fetching is determined by
   the TIMEOUT variable, which is set to 5 seconds by default.

3. Checking for Changes: After fetching data from the API,
   the module compares the current data with the previous data
   to identify any new or changed incidents.

4. Notifying Clients: If there are any changes in the incident data
   (excluding the first iteration), the WebSocket server sends a JSON
   message containing the details of the changes to all connected clients.

5. Signal Handling: The module gracefully handles termination signals
   (SIGINT and SIGTERM) to ensure a clean shutdown.

Requirements:
=============
The module relies on the following libraries:

- aiohttp
- websockets
- asyncio

API Endpoint
=============
The module accesses the API of the Status Dashboard using the URL
specified inthe environment variable API_LINK.
The default URL is http://127.0.0.1:5000/api/v1/incidents.

Configuration:
==============
The module provides some configuration options through environment variables:

TIMEOUT: The interval (in seconds) for checking changes and fetching data
from the API.
Default: 5 seconds.

REQUEST_TIMEOUT: The timeout (in seconds) for making HTTP requests to the API.
Default: 3 seconds.

LOGLEVEL: The logging level for the module. Default: "INFO".

Dockerfile
==========

.. code-block:: Dockerfile

   FROM python:3.10-alpine
   COPY requirements.txt /app/requirements.txt
   WORKDIR /app
   RUN pip install --no-cache-dir -r requirements.txt
   COPY app/ /app
   EXPOSE 8765
   CMD python server.py

WebSocket Server Usage
======================

- Establish WebSocket Connection: Clients can establish a WebSocket connection
  to the WebSocket server at the address ws://localhost:8765/.
- Receive Changes: Once connected, clients will receive real-time updates
  about incidents whenever there are changes in the incident data.
- Request Incidents: Clients can send the message "get_incidents" to the
  WebSocket server to request the current incident data. The server will
  respond with a JSON object containing the details of the incidents.
- Note: If the API of the Status Dashboard is not available during startup,
  the WebSocket server will log an error and exit.

Example Usage:

.. code-block:: shell

   >>> wscat -c ws://localhost:8765
   >>> get_incidents
      