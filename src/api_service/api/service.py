from fastapi import FastAPI, UploadFile, File


app = FastAPI(title="API Server", description="API Server", version="v1")

@app.get("/chatbot")
def experiments_fetch():
    # Fetch experiments
    return 