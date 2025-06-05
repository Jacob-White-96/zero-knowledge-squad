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

LLM_PROMPT_TEMPLATE = """You are a security auditor for smart contracts that generates a vulnerability report. You will be provided with a smart contract as Solidity code and a slither report. You must then provide the user with a one-time analysis of the code and the report and then your conversation will end. At the start of the report provide an estimated risk score out of 100. Now lets start.

Here is the Solidity source code you need to analyze:
-----------------
{solidity_code}

And here is the Slither static analysis report for that contract:
-----------------
{slither_report}

Please analyze the contract in light of the Slither report and provide a summary of the potential vulnerabilities, severity levels, and recommendations. Your output should be structured and easy to read.
"""

BASELINE_LLM_RESPONSE = """### Security Audit Report for `EtherStore` Contract

---

#### Contract Overview
- **Name**: EtherStore
- **Compiler Version**: Solidity ^0.8.0
- **Main Features**:
  - Allows users to deposit Ether.
  - Allows users to withdraw Ether, subject to:
    - A per-withdrawal limit (1 ether).
    - A cooldown period of 1 week between withdrawals.
  - Stores user balances and last withdrawal timestamps.

---

#### Findings Summary (Based on Slither Report and Manual Review)

| Severity     | Issue Description                                   | Location / Function           | Notes & Risk                                                               | Recommendation                            |
|--------------|----------------------------------------------------|------------------------------|---------------------------------------------------------------------------|------------------------------------------|
| **High**     | **Reentrancy vulnerability**                       | `withdrawFunds()`             | The external call `msg.sender.call{value: _weiToWithdraw}("")` is made **before** updating the user balance and withdrawal timestamp.
 This allows a malicious contract to re-enter `withdrawFunds` through fallback and drain more Ether than allowed if it exploits timing. | Apply the **checks-effects-interactions** pattern:
 - Update the state (`balances` and `lastWithdrawTime`) **before** making the external call.
 Alternatively, consider using `ReentrancyGuard` from OpenZeppelin. |
| **Medium**   | No major medium severity issues detected           |                              |                                                                           |                                          |
| **Low**      | Informational and style issues (e.g., no events)   | Entire contract               | No events emitted on deposit or withdrawal, which limits off-chain tracking.
 Naming and code style are simple but can improve clarity. | Add `Deposit` and `Withdrawal` events.
 Improve function and variable naming for clarity if needed.  |
| **Informational** | Use of low-level `call` for Ether transfer      | `withdrawFunds()`             | Low-level call returns a boolean for success/failure, which is checked here.
 This is acceptable in Solidity >=0.8, but `transfer` or `send` has been deprecated due to gas stipend limits. | Using `call` is correct here, but ensure proper reentrancy protection as noted. |

---

#### Detailed Analysis

1. **Reentrancy Vulnerability**

   Current flow in `withdrawFunds`:
   ```solidity
   (bool sent, ) = msg.sender.call{value: _weiToWithdraw}("");
   require(sent, "Failed to send Ether");

   balances[msg.sender] -= _weiToWithdraw;
   lastWithdrawTime[msg.sender] = block.timestamp;
   ```
   
   The external call to send Ether is made **before** updating the contract's accounting of balances and timestamps. This allows a malicious user contract to re-enter the `withdrawFunds` function during the call, before the user's balance has been reduced or withdrawal time updated, potentially withdrawing multiple times within the same block.

   **Recommended fix**:
   ```solidity
   balances[msg.sender] -= _weiToWithdraw;
   lastWithdrawTime[msg.sender] = block.timestamp;

   (bool sent, ) = msg.sender.call{value: _weiToWithdraw}("");
   require(sent, "Failed to send Ether");
   ```
   Or, even better, integrate the OpenZeppelin `ReentrancyGuard` to prevent reentrant calls altogether.

2. **Lack of Events**

   There are no events emitted for deposits or withdrawals, which hampers transparency and off-chain monitoring.

   Add events such as:
   ```solidity
   event Deposit(address indexed user, uint256 amount);
   event Withdrawal(address indexed user, uint256 amount);
   ```

   And emit them within `depositFunds` and `withdrawFunds`.

3. **Other Observations**

   - Withdrawal limit and cooldown are enforced correctly via require statements.
   - The use of Solidity version 0.8.0 mitigates some overflow problems.
   - Slither reported 1 optimization issue which likely relates to gas usage; this is not currently impacting security but could be reviewed to improve efficiency.

---

### Summary of Recommendations

| Action Item                                    | Priority  |
|------------------------------------------------|-----------|
| Fix reentrancy vulnerability by reordering state updates before external calls or use `ReentrancyGuard` | **High**  |
| Add deposit and withdrawal events for better transparency | **Medium** |
| Consider minor gas optimizations if desired    | Low       |
| Maintain use of Solidity 0.8+ to benefit from built-in overflow protection | Informational |

---

### Conclusion

The `EtherStore` contract implements basic deposit and withdrawal functionality with limits, but suffers from a **critical reentrancy vulnerability** that can lead to theft of funds. Immediate remediation is required to reorder state updates or introduce reentrancy guards. Additionally, adding events will improve transparency and traceability of contract interactions.

Implement the recommended fixes before deploying or using this contract in production environments.
"""

testing=False

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

    if testing:
        llm_summary = BASELINE_LLM_RESPONSE
    else:
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
