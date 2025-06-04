import subprocess
import tempfile
import os

def run_slither_analysis(solidity_code: str) -> str:
    with tempfile.NamedTemporaryFile(suffix=".sol", delete=False, mode="w") as tmp_file:
        tmp_file.write(solidity_code)
        tmp_path = tmp_file.name

    try:
        result = subprocess.run(
            ["slither", tmp_path, "--print", "human-summary,contract-summary,entry-points"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10
        )

        output = result.stdout.strip() or f"Slither stderr:\n{result.stderr.strip()}"

    except Exception as e:
        output = f"Slither failed: {str(e)}"

    finally:
        os.remove(tmp_path)

    return output

