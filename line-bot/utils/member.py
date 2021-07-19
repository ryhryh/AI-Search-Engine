import pytz
import pandas as pd
from datetime import datetime, timedelta, timezone
from google.cloud import datastore

class MemberUtil:
    def __init__(self, default_search_quota=50, default_days=60):
        self.default_search_quota = default_search_quota
        self.default_days = default_days
        self.datastore_client = datastore.Client()
        self.setup_rate_limit_table()
        
    def setup_user(self, studentID):
        name = studentID
        kind = 'LineUser'
        key = self.datastore_client.key(kind, name)
        user_entity = self.datastore_client.get(key)
        if user_entity == None:
            user_entity = self.create_user(studentID)
        self.user_entity = user_entity
                
    def create_user(self, studentID):
        hours = self.default_days*24
        current_time = self.get_current_time()
        rate_limit_table = self.rate_limit_table
        
        name = studentID
        kind = 'LineUser'
        key = self.datastore_client.key(kind, name)
        entity = datastore.Entity(key=key)
        
        entity['userID'] = studentID
        entity['createTime'] = current_time
        
        entity['ticketID'] = None
        entity['ticket_level'] = None
        entity['ticket_search_quota'] = self.default_search_quota
        entity['ticket_start_time'] = current_time
        entity['ticket_end_time'] = current_time + timedelta(hours=hours)
        
        entity['is_normal'] = 1
        for i in range(len(rate_limit_table)):
            end_time_name = rate_limit_table.loc[i, 'name'] + '_end_time'
            minute = int(rate_limit_table.loc[i, 'minute'])
            end_time = current_time + timedelta(minutes=minute) 
            
            search_quota_name = rate_limit_table.loc[i, 'name'] + '_search_quota'
            search_quota = int(rate_limit_table.loc[i, 'quota'])
            
            entity[end_time_name] = end_time
            entity[search_quota_name] = search_quota

        self.datastore_client.put(entity)
        return entity
    
    def get_current_time(self):
        current_time = datetime.now().replace(tzinfo=timezone.utc)
        return current_time
    
    def get_user_type(self):
        current_time = self.get_current_time()
        
        ticket_end_time = self.user_entity['ticket_end_time']
        ticket_search_quota = self.user_entity['ticket_search_quota']
        is_normal = self.user_entity['is_normal']
        
        if is_normal:
            if ticket_search_quota == 0 or current_time > ticket_end_time:
                user_type = 'pay'
            else:
                user_type = 'normal'
        else:
            user_type = 'abnormal'
        return user_type
    
    def update_GDS_LineUser(self):
        self.update_GDS_LineUser_search_quota()
        self.update_GDS_LineUser_rate_limit_end_time()
        self.datastore_client.put(self.user_entity)
    
    def update_GDS_LineUser_search_quota(self):
        rate_limit_table = self.rate_limit_table
        self.user_entity['ticket_search_quota'] -= 1
        for i in range(len(rate_limit_table)):
            search_quota_name = rate_limit_table.loc[i, 'name'] + '_search_quota'
            self.user_entity[search_quota_name] -= 1
            
            # prevent many request
            if self.user_entity[search_quota_name] == 0:
                self.user_entity['is_normal'] = 0
                
            
    def update_GDS_LineUser_rate_limit_end_time(self):
        rate_limit_table = self.rate_limit_table
        current_time = self.get_current_time()        
        for i in range(len(rate_limit_table)):
            name = rate_limit_table.loc[i, 'name']
            minute = int(rate_limit_table.loc[i, 'minute'])
            search_quota = int(rate_limit_table.loc[i, 'quota'])
            
            end_time_name = name + '_end_time'
            search_quota_name = name + '_search_quota'
            
            end_time = self.user_entity[end_time_name]
            if current_time > end_time:
                end_time = current_time + timedelta(minutes=minute) 
                self.user_entity[end_time_name] = end_time
                self.user_entity[search_quota_name] = search_quota
                        
    def setup_rate_limit_table(self):
        rate_limit_table = pd.DataFrame()
        rate_limit_table['name'] = ['minute1', 'minute5']
        rate_limit_table['minute'] = [1, 5]
        rate_limit_table['quota'] = [5, 10]
        self.rate_limit_table = rate_limit_table
        