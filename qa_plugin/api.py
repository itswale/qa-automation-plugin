from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from qa_plugin.core import QACore

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