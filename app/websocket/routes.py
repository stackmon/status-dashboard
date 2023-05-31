from flask import request
from app.websocket import bp
from app.websocket import sock
from app.models import Incident
from sqlalchemy import event

connected_clients = []

@sock.route('/ws')
def ws_handler(ws):
    connected_clients.append(ws)
    while True:
        for client in connected_clients:
            data = client.receive()
            client.send(data)
    return ''

def create_message(target):
    return {
        "id": target.id,
        "text": target.text,
        "impact": target.impact,
        "start_date": target.start_date,
        "end_date": target.end_date,
        "updates": target.updates
    }

@event.listens_for(Incident, "after_update")
def handle_incident_update(mapper, connection, target):
    message = create_message(target)
    for client in connected_clients:
        client.send(message)

@event.listens_for(Incident, "after_insert")
def handle_incident_insert(mapper, connection, target):
    message = create_message(target)
    for client in connected_clients:
        client.send(message)
