# app/main.py

from backend.main import Flask, request, jsonify

app = Flask(__name__)

@app.route("/analyze", methods=["POST"])
def analyze_contract():
    data = request.get_json()
    solidity_code = data.get("code")

    if not solidity_code:
        return jsonify({"error": "No Solidity code provided"}), 400

    # Placeholder response
    dummy_report = {
        "slither_report": "SMART CONTRACT VULNERABILITY REPORT (placeholder)",
        "llm_summary": "This contract appears to be a basic Solidity contract. No real analysis has been performed yet."
    }

    return jsonify(dummy_report)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
