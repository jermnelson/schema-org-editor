from flask import Flask
from editor import schema_editor


app = Flask(__name__)
app.register_blueprint(schema_editor)
app.config["SECRET_KEY"] = "43q0r8uscvs"

if __name__ == '__main__':
    host = '0.0.0.0'
    port = 8100
    app.run(
        host=host,
        port=port,
        debug=True)

