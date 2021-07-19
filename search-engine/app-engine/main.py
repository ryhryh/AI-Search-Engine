import os
from flask import Flask, request, jsonify

from utils import manager
managerUtil = manager.ManagerUtil(bucket_name='easy666', blob_dirname='Qa')

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_MIMETYPE'] ="application/json;charset=utf-8"

@app.route('/')
def index():
    return 'hihi'

@app.route('/search', methods=['GET', 'POST'])            
def search():
    content = request.json
    result = managerUtil.search(content)
    j = jsonify(result)
    return j

if __name__ == '__main__':
    #     app.run(host='127.0.0.1', port=8080, debug=True)    
    app.run(host="0.0.0.0", port=8787, debug=True)
    