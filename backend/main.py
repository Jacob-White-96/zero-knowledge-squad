# app.py (main Flask backend)

from flask import Flask, request, jsonify
import os, subprocess, uuid

app = Flask(__name__)
TMP_FOLDER = 'tmp_contracts'
os.makedirs(TMP_FOLDER, exist_ok=True)

@app.route("/analyze", methods=["POST"])
def analyze_contract():
    data = request.get_json()
    solidity_code = data.get("code")

    if not solidity_code:
        return jsonify({"error": "No Solidity code provided"}), 400

    # Save code to temporary .sol file
    filename = f"{TMP_FOLDER}/temp_{uuid.uuid4().hex}.sol"
    with open(filename, 'w') as f:
        f.write(solidity_code)

    # Run Slither on the saved file
    result = subprocess.getoutput(f"slither {filename}")

    # Create a dummy LLM-like summary
    llm_summary = "This is a simulated audit summary. Detected issues include common patterns like reentrancy or unguarded access."

    return jsonify({
        "slither_report": result,
        "llm_summary": llm_summary
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
