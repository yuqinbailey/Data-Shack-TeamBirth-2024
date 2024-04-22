import os
from google.cloud import storage
from fastapi import FastAPI, HTTPException
from langchain_community.vectorstores import FAISS
from langchain.embeddings import HuggingFaceInstructEmbeddings

from peft import PeftModel
from pydantic import BaseModel
import torch
from transformers import AutoModelForCausalLM, BitsAndBytesConfig, AutoTokenizer, pipeline

# Define model and bucket parameters
model_name = "daryl149/llama-2-7b-chat-hf"
fine_tuned_model = "socratic_ed_llama_2_7b"
bucket_name = "data_wa"

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

# 4. Load the adapter into the model
tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True, device_map='auto')

# 5. Create pipe for text generation
pipe = pipeline(task="text-generation", model=model, tokenizer=tokenizer, max_new_tokens=500,)

# 6. Load the context vector database
if not os.path.exists('vector_db_loaded'):
    os.makedirs('vector_db_loaded')

for f in ['index.faiss', 'index.pkl']:
    blob = bucket.blob(f'vec_db/{f}')
    blob.download_to_filename(os.path.join('vector_db_loaded', f))
db = FAISS.load_local('vector_db_loaded', embeddings=HuggingFaceInstructEmbeddings(), allow_dangerous_deserialization=True)

def generate_answer(q):
    context = db.similarity_search(q)
    # Truncate context. Shouldn't have to do this but
    # without it we often generate the empty string.
    N = 10_000
    if len(context)>N:
        context = context[:N]
    prompt = q
    result = pipe(prompt)
    answer = result[0]['generated_text'][len(prompt):].strip()
    return answer

print(generate_answer("Tell me something about the machine learning!"))