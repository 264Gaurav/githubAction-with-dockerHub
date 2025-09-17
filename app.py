from flask import Flask, jsonify

app = Flask(__name__)


@app.get("/")
def index():
    return jsonify({"message": "Hello, World!"}), 200


@app.get("/health")
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
