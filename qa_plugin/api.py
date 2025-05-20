from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from qa_plugin.core import QACore
import logging
import os
import subprocess

app = FastAPI(title="QA Automation Plugin")

class TestConfig(BaseModel):
    test_type: str = "all"
    config_path: str = "config.yaml"

@app.post("/run-tests")
async def run_tests(config: TestConfig):
    if not os.path.exists(config.config_path):
        raise HTTPException(status_code=400, detail="Config file not found")
    core = QACore(config.config_path)
    results = core.run_tests(config.test_type)
    return {"status": "success", "results": results}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

logger = logging.getLogger(__name__)

def get_results():
    try:
        return db.get_results()
    except Exception as e:
        logger.warning(f"Unable to retrieve results: {e}")
        return []

def update_results_state():
    st.session_state["results"] = get_results()

def install_playwright_browsers_if_cloud():
    # Streamlit Cloud sets 'HOME' to '/home/appuser'
    if os.environ.get("HOME", "") == "/home/appuser":
        try:
            subprocess.run(["playwright", "install", "chromium"], check=True)
        except Exception as e:
            print("Playwright browser install failed:", e)

install_playwright_browsers_if_cloud()