import os
import openai
import sys
import json

from langchain_community.embeddings import HuggingFaceInstructEmbeddings
from langchain_community.vectorstores import FAISS


from google.cloud import storage



def openai_setup(secret_path: str):
    """
    Load OpenAI API key from the secrets file
    """
    with open(secret_path) as f:
        secrets = json.load(f)

    os.environ['OPENAI_API_KEY'] = secrets['OPENAI_API_KEY']
    openai.api_key = os.environ['OPENAI_API_KEY']



client = storage.Client()
bucket = client.bucket('data_wa')
blobs = bucket.list_blobs()
for b in blobs:
    print(b.name)

# embeddings = HuggingFaceInstructEmbeddings()
# blob_vectordb = bucket.blob("data_wa/vec_db/index.faiss")
# vectordb = FAISS.load_local(blob_vectordb, embeddings, allow_dangerous_deserialization=True)

for f in ['index.faiss', 'index.pkl']:
    blob = bucket.blob(f'vec_db/{f}')
    print(blob)
    blob.download_to_filename(os.path.join('vec_db', f))
db = FAISS.load_local('vec_db', embeddings=HuggingFaceInstructEmbeddings())


retriever=db.as_retriever()

openai_setup('../secrets/openai_secret.json')

# loader = CSVLoader(file_path='./teambirth_surveys/Washington.csv')
# docs = loader.load()

# text_splitter = RecursiveCharacterTextSplitter(
#     chunk_size = 500,
#     chunk_overlap = 150,
#     separators=["\n\n", "\n", "(?<=\. )", " ", ""]
# )

# splits = text_splitter.split_documents(docs)
# embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
# vectordb = FAISS.from_documents(documents=splits, embedding=embedding)

#db.save_local("faiss_index")
#vectordb = FAISS.load_local("faiss_index", embeddings)



if __name__ == "__main__":
    
    question = input("Please enter your question: ")
    docs = retriever.invoke(question)
    print(docs)  


    