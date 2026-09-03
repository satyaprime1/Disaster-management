from flask import Flask
from flask_cors import CORS

from Backend.routes.prediction_routes import prediction_bp
from Backend.routes.satellite_routes import satellite_bp


app = Flask(__name__)

CORS(app)

app.register_blueprint(prediction_bp)
app.register_blueprint(satellite_bp)


@app.route("/health", methods=["GET"])
def health_check():
    return {
        "status": "ok",
        "message": "Backend is running"
    }, 200


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8000,
        debug=True
    )