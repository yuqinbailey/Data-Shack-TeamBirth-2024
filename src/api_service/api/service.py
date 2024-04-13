from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import httpx

# Setup FastAPI app
app = FastAPI(
    title="API Server",
    description="API Server",
    version="v1"
)
# services are running and reachable from this service.
RETRIEVAL_URL = ""
LLM_URL = ""

security = HTTPBasic()

def get_current_active_user(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials.username != "admin" or credentials.password != "secret":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

@app.post("/chatbot")
async def chat_with_bot(user_input: str, user: str = Depends(get_current_active_user)):
    # Send user input to the Retrieval container.
    try:
        retrieval_response = httpx.post(RETRIEVAL_URL, json={"input": user_input})
        retrieval_response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        # Handle error from Retrieval service.
        raise HTTPException(status_code=exc.response.status_code, detail=str(exc))

    # Assume retrieval_response.json() contains something like {"embedding": "..."}
    embedding = retrieval_response.json().get("embedding")

    # Send embedding to the LLM container.
    try:
        llm_response = httpx.post(LLM_URL, json={"embedding": embedding})
        llm_response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        # Handle error from LLM service.
        raise HTTPException(status_code=exc.response.status_code, detail=str(exc))

    # Return the LLM's generated response.
    return llm_response.json()
