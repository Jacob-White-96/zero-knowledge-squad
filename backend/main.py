from flask import Flask, request, jsonify
from flask_cors import CORS
from slither import run_slither_analysis

app = Flask(__name__)
CORS(app)

@app.route("/analyze", methods=["POST"])
def analyze_contract():
    data = request.get_json()
    solidity_code = data.get("code")

    if not solidity_code:
        return jsonify({"error": "No Solidity code provided"}), 400

    slither_report = run_slither_analysis(solidity_code)

    return jsonify({
        "slither_report": slither_report,
        "llm_summary": "This contract appears to be a basic Solidity contract. No LLM analysis has been performed yet."
    })
