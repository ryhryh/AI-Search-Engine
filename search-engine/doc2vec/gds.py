from google.cloud import datastore
import math
from datetime import datetime

class EntityUtil:
    def __init__(self, kind='Qa'):
        self.date = datetime.now().strftime("%Y-%m-%d")
        self.kind = kind
        self.datastore_client = datastore.Client()
        self.setup_todo_q()
        self.num_tfrecords = math.ceil(len(self.todo_q) / 3)  
        
    def setup_todo_q(self):
        query = self.datastore_client.query(kind=self.kind)
        query.add_filter("vector_time", "=", 'x')
        self.todo_q = list(query.fetch())
    
    def update_q(self):
        done_q = []
        for q in self.todo_q:
            q['vector_time'] = self.date
            done_q.append(q)
        self.datastore_client.put_multi(done_q)