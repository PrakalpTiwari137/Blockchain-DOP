import sys, requests
from OpenSSL import crypto
from cryptography.fernet import Fernet

def redirectToLeader(server_address, message):
    type = message["type"]
    # looping until someone tells he is the leader
    while True:
        # switching between "get" and "put"
        if type == "get":
            try:
                response = requests.get(server_address,
                                        json=message,
                                        timeout=1)
            except Exception as e:
                return e
                
        else:
            try:
                response = requests.put(server_address,
                                        json=message,
                                        timeout=1)
            except Exception as e:
                return e

        # if valid response and an address in the "message" section in reply
        # redirect server_address to the potential leader
        
        # if the message we get from client contains "payload" entry 
        # and the "payload" contains "message" entry, then we know that 
        # the client needs to redirect
        if response.status_code == 200 and "payload" in response.json():
            payload = response.json()["payload"]
            if "message" in payload:
                # payload["message"] contains the address of the LEADER
                server_address = payload["message"] + "/request"       
            else:
                break
        else:
            break
            
    return response.json()
   

# client put request
def put(addr, key, value):
    server_address = addr + "/request"
    payload = {'key': key, 'value': value}
    message = {"type": "put", "payload": payload}
    
    #encrypting the message
    file_key = open('encode_key.key', 'rb')  
    key = file_key.read()
    file_key.close()
    encoded = message["payload"]["key"].encode()
    f1 = Fernet(key)
    message_encrypt = f1.encrypt(encoded)
    message["payload"]["key"] = message_encrypt.decode()
    
    # redirecting till we find the leader, in case of request during election
    print(redirectToLeader(server_address, message))


# client get request
def get(addr, key):
    print("Inside get\n")
    server_address = addr + "/request"
    payload = {'key': key}
    message = {"type": "get", "payload": payload}
    
    # redirecting till we find the leader, in case of request during election
    print(redirectToLeader(server_address, message))


if __name__ == "__main__":
    if len(sys.argv) == 3:
        # addr, key
        # get
        addr = sys.argv[1]
        key = sys.argv[2]
        get(addr, key)
    elif len(sys.argv) == 4:
        # addr, key value
        # put
        addr = sys.argv[1]
        key = sys.argv[2]
        val = sys.argv[3]
        put(addr, key, val)
    else:
        print("PUT usage: python3 client.py address 'key' 'value'")
        print("GET usage: python3 client.py address 'key'")
        print("Format: address: http://ip:port")
