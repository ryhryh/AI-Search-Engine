from flask import Flask, request, abort, jsonify
from utils import manager

from linebot.exceptions import (
    LineBotApiError, InvalidSignatureError
)

from linebot.models import (
    MessageEvent, TextMessage, StickerMessage, LocationMessage, ImageMessage, VideoMessage, AudioMessage, FileMessage
)

app = Flask(__name__)

#####################################################################
managerUtil = manager.ManagerUtil()
managerUtil.setup_line_bot()
handler = managerUtil.handler
#####################################################################

@app.route('/')
def index():
    return "hihi"

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except LineBotApiError as e:
        print("Got exception from LINE Messaging API: %s\n" % e.message)
        for m in e.error.details:
            print("  %s: %s" % (m.property, m.message))
        print("\n")
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=(TextMessage, StickerMessage, LocationMessage, ImageMessage, VideoMessage, AudioMessage, FileMessage))
def handle_message(event):
    managerUtil.setup_event(event)
    managerUtil.handle_message()
    
if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8080, debug=True)    
#     app.run(host="0.0.0.0", port=8787, debug=True)
