from flask import Flask

app = Flask(__name__)

from app.controllers.default import bp 

app.register_blueprint(bp)