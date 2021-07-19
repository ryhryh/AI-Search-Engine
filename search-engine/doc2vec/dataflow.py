import os
import argparse
from datetime import datetime

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, SetupOptions
from apache_beam.io.gcp.datastore.v1new.datastoreio import ReadFromDatastore, WriteToDatastore
from apache_beam.io.gcp.datastore.v1new.types import Entity, Key, Query

import tensorflow_transform as tft
import tensorflow_hub as hub
import tensorflow as tf
import tensorflow_text
import tensorflow_transform.beam as tft_beam
import tensorflow_transform.coders as tft_coders
from tensorflow_transform.tf_metadata import dataset_metadata
from tensorflow_transform.tf_metadata import schema_utils

class DataflowUtil:
    def __init__(self, 
                 num_tfrecords=3,
                 project="affable-enigma-309308", 
                 bucket_name='easy666', 
                 kind='Qa',
                 blob_dirname='Qa',
                 runner="DataflowRunner", # DirectRunner
                 region="us-central1", 
                 job_name="dataflow_1", 
                 machine_type="n1-highmem-4", 
                 max_num_workers=8,
                 setup_file="./setup.py"):
        
        self.bucket_name = bucket_name
        self.blob_dirname = blob_dirname
        self.kind = kind
        self.runner = runner
        self.project = project 
        self.job_name = job_name
        self.region = region
        self.machine_type = machine_type
        self.max_num_workers = max_num_workers
        self.setup_file = setup_file
        self.num_tfrecords = num_tfrecords
        
        self.date = datetime.now().strftime("%Y-%m-%d")
        
        self.setup_args()
        self.setup_pipelineOptions()
        self.setup_tft_args()
        
    def setup_tft_args(self):
        self.transform_temp_dir = "gs://%s/%s/dataflow/transform/temp"%(self.bucket_name, self.blob_dirname)
        self.file_path_prefix = 'gs://%s/%s/embeddings/%s'%(self.bucket_name, self.blob_dirname, self.date)                
        self.file_name_suffix='.tfrecords'        
            
    def setup_args(self):
        parser = argparse.ArgumentParser()
        # parser.add_argument()
        self.known_args, self.unknown_args = parser.parse_known_args()
        
    def setup_pipelineOptions(self):
        staging_location="gs://%s/%s/dataflow/staging"%(self.bucket_name, self.blob_dirname)
        temp_location="gs://%s/%s/dataflow/temp"%(self.bucket_name, self.blob_dirname)
        
        self.pipelineOptions = PipelineOptions(
            staging_location=staging_location, 
            temp_location=temp_location,
            runner=self.runner,
            project=self.project,
            job_name=self.job_name,
            region=self.region, 
            machine_type=self.machine_type, 
            max_num_workers=self.max_num_workers, 
            setup_file=self.setup_file,
            flags=self.unknown_args,
            save_main_session=True, #!
            #streaming=True #!
        ) 
        
    def embed_text(self, text):
        module_url = 'https://tfhub.dev/google/universal-sentence-encoder-multilingual/3'
        model = hub.load(module_url)
        return model(text)
        
    def preprocess_fn(self, input_features):
        id_ = input_features['id']
        text = input_features['text']

        embedding = self.embed_text(text)

        output_features = {'id': id_,
                           'embedding': embedding}
        return output_features
    
    def get_query(self):
        filters = [('vector_time', '=', 'x')]
        query = Query(
            kind=self.kind, 
            project=self.project, 
            filters=filters #?
        )
        return query
    
    def get_metadata(self):
        feature_spec = {}
        feature_spec['id'] = tf.io.FixedLenFeature([], tf.string)
        feature_spec['text'] = tf.io.FixedLenFeature([], tf.string)

        schema = schema_utils.schema_from_feature_spec(feature_spec)
        metadata = dataset_metadata.DatasetMetadata(schema)
        return metadata

    def parse_entity(self, beam_entity):   
        datastore_entity = beam_entity.to_client_entity()
        name = datastore_entity.key.name
        question_text = datastore_entity['question_text']

        output = {'id': name,
                  'text': question_text}
        return output
    
    def run(self):
        query = self.get_query()
        p = beam.Pipeline(options=self.pipelineOptions)
        x = p | 'read from datastore' >> ReadFromDatastore(query)
                
        articles = x | "parse_entity" >> beam.Map(self.parse_entity)
        with tft_beam.Context(temp_dir=self.transform_temp_dir, force_tf_compat_v1=False):
            articles_dataset = articles, self.get_metadata()

            transformed_dataset, transform_fn = (
                articles_dataset | 'Extract embeddings' >> tft_beam.AnalyzeAndTransformDataset(self.preprocess_fn)
            )

            transformed_data, transformed_metadata = transformed_dataset
            
            transformed_data | 'Write embeddings to TFRecords'  >> beam.io.tfrecordio.WriteToTFRecord(
                file_path_prefix=self.file_path_prefix,
                file_name_suffix=self.file_name_suffix,
                coder=tft_coders.example_proto_coder.ExampleProtoCoder(transformed_metadata.schema),
                num_shards=self.num_tfrecords
            )
        
        result = p.run()        
        result.wait_until_finish()
        
if __name__ == '__main__':   
    num_tfrecords = 3
    dataflowUtil = DataflowUtil(runner="DirectRunner", num_tfrecords=num_tfrecords)
    dataflowUtil.run()
    