import os
import shutil
import argparse
import glob
# import json
import pandas as pd
from google.cloud import storage
from langchain_community.document_loaders.csv_loader import CSVLoader
# from langchain_text_splitters import CharacterTextSplitter
from langchain_experimental.text_splitter import SemanticChunker
# from langchain.embeddings.openai import OpenAIEmbeddings
# from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.embeddings import HuggingFaceInstructEmbeddings 
from langchain.vectorstores import FAISS


# def openai_setup(secret_path):
#     """
#     Load OpenAI API key from the secrets file
#     """
#     with open(secret_path) as f:
#         secrets = json.load(f)

#     os.environ['OPENAI_API_KEY'] = secrets['OPENAI_API_KEY']
#     openai.api_key = os.environ['OPENAI_API_KEY']

def get_all_files(client, bucket_name):
    blobs = client.get_bucket(bucket_name).list_blobs()
    all_files = []
    for blob in blobs:
        if blob.name.endswith(('.csv', '.xlsx', '.xls')):
            blob.download_to_filename(f'metadata/raw/{blob.name}')
            all_files.append(blob.name)
    return all_files

def load_file(file, skip_row=True):
    file_name, file_extension = os.path.splitext(file)
    if file_extension.lower() in ['.csv']:
        shutil.move(f'metadata/raw/{file}', f'metadata/processed/{file}')
        return
    df = pd.read_excel(f'metadata/raw/{file}', header=0, engine='openpyxl')
    if skip_row:
        df.drop(index=0, inplace=True)
    filtered_df = df[df['Q23'].notnull()].Q23
    filtered_df.to_csv(f'metadata/processed/{file_name}.csv', index=False, header=False)

def create_db(file_name, embedding_function):
    """
    Create a vector database and initialize the embeddings
    """
    loader = CSVLoader(f'metadata/processed/{file_name}.csv')
    documents = loader.load()
    # text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    text_splitter = SemanticChunker(embedding_function)
    docs = text_splitter.split_documents(documents)
    # print(len(docs))
    db = FAISS.from_documents(docs, embedding_function)

    return db

def upload_db(client, bucket_name, db_path):
    """
    Upload the vector database to GCS
    """
    bucket = client.get_bucket(bucket_name)
    files = glob.glob(f'{db_path}/index.*')
    for file in files:
        blob = bucket.blob(f'vec_db/{os.path.basename(file)}')
        blob.upload_from_filename(file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--name', default='data_wa', type=str, help='Name of the GCS bucket')
    parser.add_argument('-c', '--clean_up', default=True, type=bool, help='Clean up the metadata')
    args = parser.parse_args()

    os.makedirs('metadata/raw', exist_ok=True)
    os.makedirs('metadata/processed', exist_ok=True)

    client = storage.Client()
    bucket_name = args.name

    all_files = get_all_files(client, bucket_name)

    # openai_setup('../secrets/openai_secret.json')
    # embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    embeddings = HuggingFaceInstructEmbeddings()

    # NOTE: Assuming one file in the buket for now
    for file in all_files:
        load_file(file)
        file_name, file_extension = os.path.splitext(file)
        db = create_db(file_name, embeddings)
        db.save_local('metadata/vec_db')
        break

    upload_db(client, bucket_name, 'metadata/vec_db')

    # Clean up
    if args.clean_up:
        shutil.rmtree('metadata', ignore_errors=True)
