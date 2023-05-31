from flask import Blueprint
from flask_sock import Sock

sock = Sock()

bp = Blueprint('websocket', __name__)

from app.websocket import routes