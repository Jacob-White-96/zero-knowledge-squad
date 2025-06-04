document.getElementById('analyzeBtn').addEventListener('click', async () => {
  const code = document.getElementById('codeInput').value;

  const res = await fetch('http://localhost:5000/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code }),
  });

  const result = await res.text();
  document.getElementById('reportOutput').textContent = result;
});




