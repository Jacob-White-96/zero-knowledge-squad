from flask import Flask, request, jsonify
from flask_cors import CORS
from slither import run_slither_analysis
from dotenv import load_dotenv
from openai import OpenAI
import os

load_dotenv()  # Load API keys from .env

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)
CORS(app)

LLM_PROMPT_TEMPLATE = """You are a security auditor for smart contracts. You will be provided with a smart contract as Solidity code and a slither report. You must then provide the user with an analysis of the code and the report, the user will see your report and the slither report side by side. Now lets start.

Here is the Solidity source code you need to analyze:
-----------------
{solidity_code}

And here is the Slither static analysis report for that contract:
-----------------
{slither_report}

Please analyze the contract in light of the Slither report and provide a summary of the potential vulnerabilities, severity levels, and recommendations. Your output should be structured and easy to read.
"""

@app.route("/analyze", methods=["POST"])
def analyze_contract():
    data = request.get_json()
    solidity_code = data.get("code")

    if not solidity_code:
        return jsonify({"error": "No Solidity code provided"}), 400

    # Step 1: Run Slither
    slither_report = run_slither_analysis(solidity_code)

    # Step 2: Prepare LLM prompt
    prompt = LLM_PROMPT_TEMPLATE.format(
        solidity_code=solidity_code,
        slither_report=slither_report
    )

    try:
        # Step 3: Call OpenAI LLM
        response = client.responses.create(
            model="gpt-4.1-mini-2025-04-14",
            input=prompt
        )
        llm_summary = response.output_text

    except Exception as e:
        llm_summary = f"LLM call failed: {str(e)}"

    # Step 4: Return response
    return jsonify({
        "slither_report": slither_report,
        "llm_summary": llm_summary
    })
