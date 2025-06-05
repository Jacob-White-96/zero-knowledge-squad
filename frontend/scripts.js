document.getElementById("analyzeBtn").addEventListener("click", async () => {
  const code = document.getElementById("codeInput").value;

  if (!code.trim()) {
    alert("Please paste some Solidity code!");
    return;
  }

  try {
    const response = await fetch("http://localhost:5000/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code }),
    });

    if (!response.ok) {
      throw new Error("Server error");
    }

    const data = await response.json();

    const report = data.slither_report || "No report available.";
    const summary = data.llm_summary || "No summary available.";

    // 🚨 Calculate Risk Score
    const riskScore = calculateRiskScore(report);

    // ✅ Show Risk Score Bar
    const scoreFill = document.getElementById("scoreBarFill");
    const scoreLabel = document.getElementById("scoreLabel");
    const scoreBar = document.querySelector(".risk-score-bar");

    if (scoreFill && scoreLabel && scoreBar) {
      scoreFill.style.width = `${riskScore}%`;
      scoreLabel.innerText = `${riskScore}/100`;

      if (riskScore >= 80) {
        scoreFill.style.background = "green";
      } else if (riskScore >= 50) {
        scoreFill.style.background = "orange";
      } else {
        scoreFill.style.background = "red";
      }
      scoreBar.style.display = "block";
    }

    // ✅ Enhanced Output With Fix Suggestions
    let enhancedReport = '';
    report.split('\n').forEach(line => {
      const suggestion = getFixSuggestion(line);
      const highlightedLine = line
        .replace(/ERROR/g, '<span style="color:red;font-weight:bold">ERROR</span>')
        .replace(/WARNING/g, '<span style="color:orange;font-weight:bold">WARNING</span>')
        .replace(/INFO/g, '<span style="color:blue;font-weight:bold">INFO</span>');
      enhancedReport += highlightedLine + (suggestion ? `<br><em>${suggestion}</em>` : '') + '<br><br>';
    });

    document.getElementById("reportOutput").innerHTML = `
      ${marked.parse(summary)}<br><br>
      <strong>Slither Report:</strong><br>${enhancedReport}
    `;


    // ✅ Store full report for download
    const plainEnhanced = enhancedReport
      .replace(/<[^>]+>/g, '')  // Remove HTML tags for clean PDF
      .replace(/<br>/g, '\n');  // Convert <br> to line breaks

    window.fullReport = `${summary}\n\nSlither Report:\n${plainEnhanced}`;


    document.getElementById("downloadBtn").style.display = "inline-block";

  } catch (err) {
    document.getElementById("reportOutput").innerText = "Error analyzing contract.";
    console.error(err);
  }
});

function calculateRiskScore(report) {
  const warnings = (report.match(/WARNING/g) || []).length;
  const errors = (report.match(/ERROR/g) || []).length;
  const infos = (report.match(/INFO/g) || []).length;

  let score = 100 - (warnings * 5 + errors * 10 + infos * 2);
  return Math.max(score, 0);
}

function getFixSuggestion(line) {
  if (line.includes("Reentrancy")) {
    return "🛠️ Suggestion: Use a reentrancy guard (e.g. OpenZeppelin's ReentrancyGuard).";
  }
  if (line.includes("shadowing")) {
    return "🛠️ Suggestion: Rename your variable to avoid name conflict.";
  }
  if (line.includes("overflow")) {
    return "🛠️ Suggestion: Use SafeMath or built-in overflow checks.";
  }
  return "";
}

document.getElementById("downloadBtn").onclick = () => {
  const { jsPDF } = window.jspdf;
  const doc = new jsPDF();

  const content = window.fullReport || "No report available.";

  const lines = doc.splitTextToSize(content, 180); // Auto-wrap
  doc.text(lines, 15, 20);

  doc.save("audit_report.pdf");
};

