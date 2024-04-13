import os
import argparse
import glob
import shutil

from langchain_community.vectorstores import FAISS
from langchain.embeddings import HuggingFaceInstructEmbeddings

from google.cloud import storage


def download_db(client, bucket_name, destination_dir):
    """
    Download files from GCS
    """
    bucket = client.get_bucket(bucket_name)
    blobs = bucket.list_blobs()
    for blob in blobs:
        filename = os.path.basename(blob.name)
        local_file_path = os.path.join(destination_dir, filename)
        blob.download_to_filename(local_file_path)


def upload_file_to_gcs(bucket_name, file_path, destination_blob_name):
    """
    Upload a file to Google Cloud Storage
    """
    bucket = client.get_bucket(bucket_name)

    files = glob.glob(f'{file_path}/*.txt')
    for file in files:
        blob = bucket.blob(f'retrieval/{os.path.basename(file)}')
        blob.upload_from_filename(file)


def generate_context(q, out):
    context = db.similarity_search(q)

    with open(os.path.join("retrieval_upload/", out), 'w') as f:
        for item in context:
            f.write("%s\n" % item.page_content)
            

if __name__ == "__main__": 
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--name', default='data_wa', type=str, help='Name of the GCS bucket')
    parser.add_argument('-c', '--clean_up', default=True, type=bool, help='Clean up the metadata')
    
    parser.add_argument('-q', '--question', type=str, required=True, help='Question to generate context for')
    parser.add_argument('-o', '--output_file', type=str, required=True, help='Output file to save context')
    args = parser.parse_args()
    
    client = storage.Client()
#    bucket = client.bucket('data_wa')
    bucket_name = args.name

    for f in ['index.faiss', 'index.pkl']:
        blob = bucket_name.blob(f'vec_db/{f}')
        blob.download_to_filename(os.path.join('vectorstores/', f))
    db = FAISS.load_local('vectorstores/', embeddings=HuggingFaceInstructEmbeddings(), allow_dangerous_deserialization=True)

    generate_context(args.question, args.output_file)
    upload_file_to_gcs(bucket_name, './retrieval_upload', args.output_file)



    