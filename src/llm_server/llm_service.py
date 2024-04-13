import os
from google.cloud import storage
from fastapi import FastAPI, HTTPException
from langchain_community.embeddings import HuggingFaceInstructEmbeddings
from langchain_community.vectorstores import FAISS
#from langchain.embeddings import HuggingFaceInstructEmbeddings 
#from langchain.vectorstores import FAISS
from peft import PeftModel
from pydantic import BaseModel
import torch
from transformers import AutoModelForCausalLM, BitsAndBytesConfig, AutoTokenizer, pipeline

# Define model and bucket parameters
model_name = "daryl149/llama-2-7b-chat-hf"
fine_tuned_model = "socratic_ed_llama_2_7b"
bucket_name = "socratic_ed_bot"
adapter_directory = "./adapter_files"  # Local directory to save the downloaded adapter files
adapter_files = ["adapter_config.json", "adapter_model.bin"]

# 1. Define the necessary configurations for the quantized model
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16
)

# 2. Load the quantized base model
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=bnb_config,
    device_map='auto'
)

# 3. Download the adapter files from the GCP bucket
storage_client = storage.Client()
bucket = storage_client.bucket(bucket_name)
if not os.path.exists(adapter_directory):
    os.makedirs(adapter_directory)

for adapter_file in adapter_files:
    blob = bucket.blob(f"adapters/{fine_tuned_model}/{adapter_file}")
    blob.download_to_filename(os.path.join(adapter_directory, adapter_file))

# 4. Load the adapter into the model
adapted_model = PeftModel.from_pretrained(model, './adapter_files')
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True, device_map='auto')

# 5. Create pipe for text generation
pipe = pipeline(task="text-generation", model=model, tokenizer=tokenizer, max_new_tokens=500,)
pipe.model = adapted_model # hack: https://github.com/huggingface/peft/issues/218

# 6. Load the context vector database
if not os.path.exists('vector_db_loaded'):
    os.makedirs('vector_db_loaded')

for f in ['index.faiss', 'index.pkl']:
    blob = bucket.blob(f'data/vector_db/{f}')
    blob.download_to_filename(os.path.join('vector_db_loaded', f))
db = FAISS.load_local('vector_db_loaded', embeddings=HuggingFaceInstructEmbeddings())

def generate_answer(q):
    context = db.similarity_search(q)
    # Truncate context. Shouldn't have to do this but
    # without it we often generate the empty string.
    N = 10_000
    if len(context)>N:
        context = context[:N]
    prompt = f'''[INSTRUCTIONS]:\nYou are an educator supporting students on a discussion \
    board for a course in Data Science at Harvard by answering questions like the one below. \
    When you don't have information about some aspect of course policy from the provided relevant information, \
    you MUST NOT make any unfounded assertion. \
    You should instead advise students to message the course helpline, cs109a2023@gmail.com, \
    if you lack the required information, \
    but you must not imply that the course policies or deadlines are negotiable. \
    These are final unless there is a medical or other university excused exception.\
    You should begin your responses with a brief, friendly greeting so as to not appear curt. \
    Empty answers are never acceptable; You must provide some kind of meaningful response. \
    Most importantly, you must NEVER contradict yourself or the provided relevant information as it pertains to course policy.\n\n\
    [RELEVANT INFORMATION]: {context}\n\n\
    [QUESTION]:\n{q}\n\n\
    [ANSWER]:\n'''
    result = pipe(prompt)
    answer = result[0]['generated_text'][len(prompt):].strip()
    return answer

# Init FastAPI
app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "LLM Service Running"}

class QuestionPayload(BaseModel):
    question: str

@app.post("/generate")
def generate_response(query: QuestionPayload):
    try:
        return generate_answer(query.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
