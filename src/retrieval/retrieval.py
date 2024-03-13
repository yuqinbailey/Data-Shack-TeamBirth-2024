import os
import openai
import sys
import json

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS


from google.cloud import storage


client = storage.Client()
bucket = client.bucket('team-birth-2024')

blob_df = bucket.blob("data_wa/vec_db/wlasl_test_new.csv")
train_df = pd.read_csv(blob_df.open())

print("\n\n... LOAD SIGN TO PREDICTION INDEX MAP FROM JSON FILE ...\n")
# Read character to prediction index
blob_json = bucket.blob("data/WLASL-data/sign_to_prediction_index_map.json")
with blob_json.open("r") as f:
    json_file = json.loads(f.read())



def openai_setup(secret_path: str):
    """
    Load OpenAI API key from the secrets file
    """
    with open(secret_path) as f:
        secrets = json.load(f)

    os.environ['OPENAI_API_KEY'] = secrets['OPENAI_API_KEY']
    openai.api_key = os.environ['OPENAI_API_KEY']



openai_setup('../secrets/openai_secret.json')

loader = CSVLoader(file_path='./teambirth_surveys/Washington.csv')
docs = loader.load()

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size = 500,
    chunk_overlap = 150,
    separators=["\n\n", "\n", "(?<=\. )", " ", ""]
)

splits = text_splitter.split_documents(docs)
embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectordb = FAISS.from_documents(documents=splits, embedding=embedding)

#db.save_local("faiss_index")
#vectordb = FAISS.load_local("faiss_index", embeddings)

retriever=vectordb.as_retriever()

if __name__ == "__main__":
    
    question = input("Please enter your question: ")
    docs = retriever.invoke(question)
    print(docs)  

    