from node import Node
from node import FOLLOWER, LEADER
from flask import Flask, request, jsonify
import sys
import logging
from OpenSSL import crypto
from cryptography.fernet import Fernet


app = Flask(__name__) # creating the Flask class object
					  # __name__ is the current module


# @app.route("/path") : everytime the application receives 
# a request where the path is "/path" the corresponding 
# function will be invoked to complete the request.

@app.route("/request", methods=['GET'])
def value_get():
	# request payload is the data normally sent by a POST or PUT request
    payload = request.json["payload"]  
    reply = {"code": 'fail', 'payload': payload}
    
    # if client requests for data from LEADER
    if n.status == LEADER:
        # data retrieved using handle_get and stored in result
        # on failure handle_get() returns None
        result = n.handle_get(payload)
        if result:
            reply = {"code": "success", "payload": result}
    
    # if client requests data from FOLLOWER
    # we need to send a message to client so that it can redirect to LEADER
    elif n.status == FOLLOWER:
        reply["payload"]["message"] = n.leader
    
    return jsonify(reply)


@app.route("/request", methods=['PUT'])
def value_put():
	# message to store in database is extracted to payload
    payload = request.json["payload"]
    reply = {"code": 'fail'}

    #client verification step
    val1 = payload["key"].encode()
    try:
        file_key = open('encode_key.key', 'rb')
        key = file_key.read()
        file_key.close()
        f1 = Fernet(key)
        decrypted = f1.decrypt(val1)
        payload["key"] = decrypted.decode()
        
    except:
        reply = {"code": 'Decryption error'}
        return jsonify(reply)
	        
    # if the Node n to which client sent data is a LEADER
    if n.status == LEADER:
        # call handle_put() method to put the data into database
        # on success handle_put() returns true
        result = n.handle_put(payload)
        if result:
            reply = {"code": "success"}
    
    # if the Node n to which client sent data is a FOLLOWER
    # we need to send a message to client so that it can redirect to LEADER
    elif n.status == FOLLOWER:
        # add "message" field in payload
        # add "payload" field in reply
        payload["message"] = n.leader
        reply["payload"] = payload
    
    # send the reply to client    
    return jsonify(reply)


# we reply to vote request
@app.route("/vote_req", methods=['POST'])
def vote_req():
    # also need to let me know whether up-to-date or not
    term = request.json["term"]
    commitIdx = request.json["commitIdx"]
    staged = request.json["staged"]
    choice, term = n.decide_vote(term, commitIdx, staged)
    message = {"choice": choice, "term": term}
    print("MESSAGE vote_req = ", message)
    return jsonify(message)


@app.route("/heartbeat", methods=['POST'])
def heartbeat():
    term, commitIdx = n.heartbeat_follower(request.json)
    # return anyway, if nothing received by leader, we are dead
    message = {"term": term, "commitIdx": commitIdx}
    return jsonify(message)


# disable flask logging
log = logging.getLogger('werkzeug')
log.disabled = True

if __name__ == "__main__":
    # python server.py index ip_list
    if len(sys.argv) == 3:
        index = int(sys.argv[1])
        ip_list_file = sys.argv[2]
        ip_list = []
        # open ip list file and parse all the ips
        with open(ip_list_file) as f:
            for ip in f:
                ip_list.append(ip.strip())
        my_ip = ip_list.pop(index)

        http, host, port = my_ip.split(':')
        # initialize node with ip list and its own ip
        n = Node(ip_list, my_ip)
        app.run(host="0.0.0.0", port=int(port), debug=False)
    else:
        print("usage: python server.py <index> <ip_list_file>")
