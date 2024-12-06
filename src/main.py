import asyncio
import random
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from llm_telemetry import LLMTelemetry
from config import setup_telemetry

# Initialize OpenTelemetry
setup_telemetry()

# Initialize FastAPI and LLM Telemetry
app = FastAPI()
llm_telemetry = LLMTelemetry()

class PromptRequest(BaseModel):
    prompt: str
    model: str = "gpt-3.5-turbo"

# Simulate LLM call
async def mock_llm_call(prompt: str, model: str) -> str:
    # Simulate random latency
    await asyncio.sleep(random.uniform(0.1, 2.0))
    
    # Simulate random errors
    if random.random() < 0.1:  # 10% chance of error
        raise Exception("LLM Service Unavailable")
    
    return f"Mocked response for prompt: {prompt}"

@app.post("/generate")
async def generate_response(request: PromptRequest):
    @llm_telemetry.instrument_llm_call(request.prompt, request.model)
    async def _generate():
        return await mock_llm_call(request.prompt, request.model)
    
    try:
        response = await _generate()
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)