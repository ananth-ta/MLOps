import os

from flask import Flask, jsonify

app = Flask(__name__)

# Set at deploy time (see scripts/deploy.sh) so each revision can identify itself
APP_VERSION = os.environ.get("APP_VERSION", "dev")
GREETING = os.environ.get("GREETING", "Hello, World!")


@app.route("/")
def hello_world():
    # K_REVISION is set automatically by Cloud Run; it shows which revision served the request
    return jsonify(
        message=GREETING,
        version=APP_VERSION,
        revision=os.environ.get("K_REVISION", "local"),
    )


@app.route("/health")
def health():
    return jsonify(status="ok")


if __name__ == "__main__":
    # Local development only; in the container gunicorn serves the app (see Dockerfile)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
