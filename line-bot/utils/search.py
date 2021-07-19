import requests
import base64
import json

class SearchUtil:
    def __init__(self):
        pass
    
    def search_question(self, studentID, b2_bytes):
        # imageData
        
        b64_bytes = self.b2bytes_to_b64bytes(b2_bytes)
        b64_text = b64_bytes.decode("utf-8") # bytes2text(b64_bytes)

        request_body = {}
        request_body['studentID'] = studentID # 'student-linebot'
        request_body['imageData'] = b64_text 

        url = "https://search-question-dot-praxis-electron-301404.dt.r.appspot.com/search_question"
        payload = json.dumps(request_body)
        headers = {'content-type': "application/json"}
        response = requests.request("POST", url, data=payload, headers=headers)
        return_body = json.loads(response.text)

        answerArray = return_body['answerArray']
        answer = answerArray[0]

        q_url = self.get_questionImagePath(answer)
        a_url = self.get_answerImagePath(answer)

        return q_url, a_url

    def b2bytes_to_b64bytes(self, b2bytes):
        b64bytes = base64.b64encode(b2bytes)
        return b64bytes

    def get_questionImagePath(self, answer):
        questionID = answer['questionID']
        url = 'https://storage.googleapis.com/easy668/imageFile/%s'%(questionID)
        return url

    def get_answerImagePath(self, answer):
        a1 = {}
        a1['answerID'] = answer['answerID']
        a1['stepIDArray'] = answer['stepIDArray'] 
        request_body = [a1]

        url = 'https://asia-northeast2-praxis-electron-301404.cloudfunctions.net/get_stepArray'
        payload = json.dumps(request_body)
        headers = {'content-type': "application/json"}
        response = requests.request("POST", url, data=payload, headers=headers)
        return_body = json.loads(response.text)

        answerArray = return_body['result']
        answer = answerArray[0]
        stepArray = answer['stepArray']
        step = stepArray[0]
        stepDetailArray = step['stepDetailArray']
        stepDetail = stepDetailArray[0]
        answerImagePath = stepDetail['answserImagePath'] # answserImagePath 字打錯
        return answerImagePath
    
        