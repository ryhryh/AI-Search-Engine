from utils import member, ticket, search
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.models import (
    MessageEvent, TextMessage, StickerMessage, LocationMessage, ImageMessage, VideoMessage, AudioMessage, FileMessage, TextSendMessage, ImageSendMessage
)


class ManagerUtil:
    def __init__(self):
        self.memberUtil = member.MemberUtil()
        self.ticketUtil = ticket.TicketUtil()
        self.searchUtil = search.SearchUtil()
        self.line_teacher = 'https://lin.ee/vBlZxBF'
        self.line_service = 'https://lin.ee/XpbrUnI'
        
    def setup_line_bot(self):
        channel_secret = '7f8ac1b4e86b97aff37c09c5ee2ebead'
        self.handler = WebhookHandler(channel_secret)

        channel_access_token = 'YJhR/xR7YkbnhVaxKzaPehNFh5w/RR+Ye7cUqNxfxQYAXDb4R4ZgKrDu1bgElC+tSxFzPWNdDmcC8gqEC607TTHNW37Y7ApHWxIxEv60+mEoXrNIckZvRtyTggEKml+ZzJm+GtOZJPyU0bJr6gEuAAdB04t89/1O/w1cDnyilFU='
        self.line_bot_api = LineBotApi(channel_access_token)
        
    def setup_event(self, event):
        self.event = event
        self.reply_token = event.reply_token
        self.studentID = event.source.user_id
        self.memberUtil.setup_user(self.studentID) # O(1)
        
    def handle_message(self):
        user_type = self.memberUtil.get_user_type() # pay, normal, abnormal
        if user_type == 'normal':
            if isinstance(self.event.message, ImageMessage):
                self.handle_image()
            elif isinstance(self.event.message, TextMessage):  
                self.handle_text(text="可以把不會的題目拍起來傳給我們，我們就會回傳解答給你喔～")
            else:
                self.reply_text(text="可以把不會的題目拍起來傳給我們，我們就會回傳解答給你喔～") 
                
        elif user_type == 'pay':
            self.handle_text(text="填問卷拿好學問序號，就能繼續找解答囉～ https://forms.gle/vNuyhQCTCrs14hkN9")
            
        elif user_type == 'abnormal':
            self.reply_text(text="系統異常，請洽詢好學問客服～ %s"%(self.line_service)) 
    
    def handle_image(self):
        message_content = self.line_bot_api.get_message_content(self.event.message.id)
        b2_bytes = message_content.content 

        # 確認server有開
        try:
            q_url, a_url = self.searchUtil.search_question(self.studentID, b2_bytes)

            m1 = ImageSendMessage(q_url, q_url)
            m2 = ImageSendMessage(a_url, a_url)
            m3 = TextSendMessage(text="如果看不懂的話，可以到這裡問老師～ %s"%(self.line_teacher))

            messages = [m1, m2, m3]
            self.line_bot_api.reply_message(self.reply_token, messages)

            # 回傳之後再update
            self.memberUtil.update_GDS_LineUser() 

        except Exception as e:
            self.reply_text(text="搜尋引擎休息中，可以到這裡問老師～ %s"%(self.line_teacher)) 
            
    def handle_text(self, text=""):
        # 確認是不是ticket，不是的話就回同一句話
        if isinstance(self.event.message, TextMessage):  
            ticketID = self.event.message.text
            ticket = self.ticketUtil.get_ticket(ticketID)
            if ticket!=None:
                self.handle_ticket(ticket)
            else:
                self.reply_text(text=text) 
        else:
            self.reply_text(text=text) 
            
    def handle_ticket(self, ticket):
        is_used = self.ticketUtil.ticket_is_used(ticket)
        if is_used == True:
            self.reply_text(text="這個好學問序號已經使用過囉～") 
        else:
            activate_info = self.ticketUtil.get_activate_info(self.studentID, ticket)

            ticketID = activate_info['ticketID']
            ticket_start_time = activate_info['ticket_start_time'].strftime('%Y-%m-%d')
            ticket_end_time = activate_info['ticket_end_time'].strftime('%Y-%m-%d')

            text = '好學問序號 %s 已經開通，使用期間為 %s 至 %s。'%(ticketID, ticket_start_time, ticket_end_time)
            self.reply_text(text=text) 

            # 回傳之後再update
            self.ticketUtil.update_GDS_Ticket(activate_info)
            self.ticketUtil.update_GDS_LineUser(activate_info)
            
    def reply_text(self, text=""):
        text_message = TextSendMessage(text=text)
        messages = [text_message]
        self.line_bot_api.reply_message(self.reply_token, messages)
        
        
        