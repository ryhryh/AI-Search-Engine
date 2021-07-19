from google.cloud import datastore
import pandas as pd
from datetime import datetime, timedelta, timezone
import pytz

class TicketUtil:
    def __init__(self):
        self.datastore_client = datastore.Client()
        
    def get_ticket(self, ticketID):
        key = self.datastore_client.key('Ticket', ticketID)
        ticket = self.datastore_client.get(key)
        return ticket
    
    def ticket_is_used(self, ticket):
        userID = ticket['userID']
        is_used = (userID!=None)
        return is_used
    
    def get_current_time(self):
        current_time = datetime.now().replace(tzinfo=timezone.utc)
        return current_time
    
    def get_activate_info(self, studentID, ticket):
        ticket_level = ticket['ticket_level']
        
        ticket_level_table = self.get_ticket_level_table()
        c = (ticket_level_table.ticket_level ==ticket_level)
        ticket_level_table = ticket_level_table[c]
        
        days = ticket_level_table.days.values[0]
        hours = int(days * 24)
        ticket_search_quota = int(ticket_level_table.ticket_search_quota.values[0]) #! 要累加上一期的嗎
        
        ticketID = ticket['ticketID']
        ticket_start_time = self.get_current_time()
        ticket_end_time = ticket_start_time + timedelta(hours=hours)
        
        activate_info = {}
        activate_info['userID'] = studentID
        activate_info['ticket_level'] = ticket_level
        activate_info['ticket_search_quota'] = ticket_search_quota
        activate_info['ticketID'] = ticketID
        activate_info['ticket_start_time'] = ticket_start_time
        activate_info['ticket_end_time'] = ticket_end_time
        return activate_info

    def update_GDS_Ticket(self, activate_info):
        ticketID = activate_info['ticketID']
        key = self.datastore_client.key('Ticket', ticketID)
        entity = self.datastore_client.get(key)
        entity['userID'] = activate_info['userID']
        entity['ticket_start_time'] = activate_info['ticket_start_time']
        entity['ticket_end_time'] = activate_info['ticket_end_time']
        self.datastore_client.put(entity)
        
    def update_GDS_LineUser(self, activate_info):
        userID = activate_info['userID']
        key = self.datastore_client.key('LineUser', userID)
        entity = self.datastore_client.get(key)
        entity['ticket_level'] = activate_info['ticket_level']
        entity['ticket_search_quota'] = activate_info['ticket_search_quota']
        entity['ticketID'] = activate_info['ticketID']
        entity['ticket_start_time'] = activate_info['ticket_start_time']
        entity['ticket_end_time'] = activate_info['ticket_end_time']
        self.datastore_client.put(entity)
    
    def get_ticket_level_table(self):
        df = pd.DataFrame()
        df['ticket_level'] = ['A', 'B']
        df['days'] = [30, 30]
        df['ticket_search_quota'] = [20, 150] #[20, 150]
        return df
        
        