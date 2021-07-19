import os
import pickle
import uuid
import base64
import threading
from datetime import datetime

from annoy import AnnoyIndex
import tensorflow as tf
import tensorflow_text
import tensorflow_hub as hub
from google.cloud import storage, datastore, vision

class ManagerUtil:
    def __init__(self, 
                 bucket_name='easy666', 
                 blob_dirname='Qa', 
                 index_name='index.ann', 
                 mapping_name='mapping.pickle', 
                 temp_dir='/tmp', 
                 kind='Qa', 
                 language_list=['zh-Hant', 'en']):
        
        self.index_name = index_name
        self.mapping_name = mapping_name
        self.bucket_name = bucket_name
        self.blob_dirname = blob_dirname
        self.temp_dir = temp_dir
        self.kind = kind
        self.language_list = language_list
        
        self.storage_client = storage.Client()
        self.vision_client = vision.ImageAnnotatorClient()
        self.datastore_client = datastore.Client()
        
        self.setup_GCS()
        self.setup_classifier()
        self.setup_encoder()
        
    def search(self, content):
        image_base64_str = content['image_base64_str']
        base2_bytes = base64.b64decode(image_base64_str)
        text = self.detect_text(base2_bytes)
        query_vec = self.extract_embeddings(text)
        names = self.find_similar_items(query_vec, num_matches=3)
        question_list = self.get_items(names=names)

        image_id = str(uuid.uuid4().hex)
        content['image_ID'] = image_id
        content['is_public'] = True
        content['base2_bytes'] = base2_bytes
        content['question_id_list'] = names #!
        content['image_text'] = text
        
        self.do_async(target=self.upload_to_GCS_search_image_file, content=content)
        self.do_async(target=self.save_to_GDS_SearchHistory, content=content)
        
        result = {}
        result['image_url'] = 'https://storage.googleapis.com/%s/search_image_file/%s'%(self.bucket_name, image_id)
        result['question_list'] = question_list
        output_result = self.get_output_result(result)
        return output_result
    
    def get_output_result(self, result):
        question_list_ = []
        for q in result['question_list']:
            output_q = {}
            output_q['fb_url'] = q['fb_url']
            output_q['question_url'] = 'https://storage.googleapis.com/%s/image_file/%s'%(self.bucket_name, q['question_id'])
            output_q['answer_url'] = 'https://storage.googleapis.com/%s/image_file/%s'%(self.bucket_name, q['answer_id'])
            question_list_.append(output_q)
        result['question_list'] = question_list_
        return result
    
    def upload_to_GCS_search_image_file(self, content={}):
        image_ID = content['image_ID']
        is_public = content['is_public']
        base2_bytes = content['base2_bytes']
        
        blob_name = os.path.join('search_image_file', image_ID)
        blob = self.bucket.blob(blob_name)
        blob.upload_from_string(base2_bytes, content_type='image/png')
        if is_public: 
            blob.make_public()  
        return image_ID 
    
    def save_to_GDS_SearchHistory(self, content={}):
        image_ID = content['image_ID']
        
        kind='SearchHistory'
        name = image_ID
        complete_key = self.datastore_client.key(kind, name)
        task = datastore.Entity(key=complete_key)
        task['image_ID'] = image_ID
        task['created_time'] = datetime.now()
        task['user_id'] = content['user_id']
        task['platform'] = content['platform']
        task['image_text'] = content['image_text']
        task['question_id_list'] = content['question_id_list']
        self.datastore_client.put(task)
        
    def do_async(self, target=None, content={}):
        kwargs = {'content': content}
        threads = threading.Thread(target=target, kwargs=kwargs)
        threads.start()
        
    def detect_text(self, image_bytes):    
        image = vision.Image(content=image_bytes)
        image_context={"language_hints": self.language_list}
        r = self.vision_client.text_detection(
            image=image, 
            image_context=image_context, #!
        )
        text_annotations = r.text_annotations
        description = text_annotations[0].description if len(text_annotations) != 0 else 'xxx' #!
        return description
    
    def get_items(self, names=[]):
        keys = [self.datastore_client.key(self.kind, name) for name in names]
        items = self.datastore_client.get_multi(keys)
        
        name2entity = {item.key.name:item for item in items}
        sort_items = [name2entity[name] for name in names]
        return sort_items
        
    def setup_encoder(self):
        MODEL_URL = 'https://tfhub.dev/google/universal-sentence-encoder-multilingual/3'
        self.encoder = hub.load(MODEL_URL)
        
    def extract_embeddings(self, text):
        docs = [text]
        vecs = self.encoder(docs)   
        vec = vecs[0]
        return vec
        
    def setup_classifier(self, vector_length=512):
        index_path = os.path.join(self.temp_dir, self.index_name)
        mapping_path = os.path.join(self.temp_dir, self.mapping_name)
        
        self.index = AnnoyIndex(vector_length)
        self.index.load(index_path, prefault=True)
        
        with open(mapping_path, 'rb') as handle:
            self.mapping = pickle.load(handle)
            
    def find_similar_items(self, vector, num_matches=3):
        annoy_ids = self.index.get_nns_by_vector(vector, num_matches, search_k=-1, include_distances=False)
        datastore_names = [self.mapping[annoy_id] for annoy_id in annoy_ids]
        return datastore_names
        
    def setup_GCS(self):
        self.bucket = self.storage_client.bucket(self.bucket_name)
        self.download_file_from_GCS('%s/index/%s'%(self.blob_dirname, self.index_name)) # 'Qa/index/index.ann'
        self.download_file_from_GCS('%s/index/%s'%(self.blob_dirname, self.mapping_name)) # 'Qa/index/mapping.pickle'
        
    def download_file_from_GCS(self, blob_name='Qa/index/index.ann'):
        blob = self.bucket.blob(blob_name)
        local_path = os.path.join(self.temp_dir, os.path.basename(blob_name)) # '/tmp/index.ann'
        blob.download_to_filename(local_path)
    