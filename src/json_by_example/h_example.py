#MIME: is the translator that sits in the middle. It converts complex data into a
# text format so computers can send it, and then turns it back into a readable
# object when a user receives it.
import json
from email.message import EmailMessage#"Go to Python's email library, open the message file, and bring me the EmailMessage tool so I can start building an email."
from ipaddress import IPv4Address#IPv4Address converts an IP address written by humans (like "192.168.1.1") into a Python IP object that the computer can understand and work with safely.
from urllib.parse import ParseResult#it is  use it to split link(url) into components(name/value)
#Ex
'''urllib_parse_urlsplit.py
from urllib.parse import urlsplit

url = 'http://user:pwd@NetLoc:80/p1;para/p2;para?query=arg#frag'
parsed = urlsplit(url)
print(parsed)
print('scheme  :', parsed.scheme)
print('netloc  :', parsed.netloc)
print('path    :', parsed.path)
print('query   :', parsed.query)
print('fragment:', parsed.fragment)
print('username:', parsed.username)
print('password:', parsed.password)
print('hostname:', parsed.hostname)
print('port    :', parsed.port)
Since the parameters are not split out, the tuple API will show five elements instead of six, and there is no params attribute.

$ python3 urllib_parse_urlsplit.py

SplitResult(scheme='http', netloc='user:pwd@NetLoc:80',
path='/p1;para/p2;para', query='query=arg', fragment='frag')
scheme  : http
netloc  : user:pwd@NetLoc:80
path    : /p1;para/p2;para
query   : query=arg
fragment: frag
username: user
password: pwd
hostname: netloc
port    : 80'''

data = """{
    "sender": {
        "__class": "EmailMessage",
        "headers": {
            "From": "admin@example.com",
            "To": "user@client.com",
            "Subject": "Access Granted"
        },
        "body": "Welcome! Your access has been granted. Click the link below."
    },
    "client_ip": {
        "__class": "IPv4Address",
        "address": "192.168.1.42"
    },
    "link": {
        "__class": "ParseResult",
        "scheme": "https",
        "netloc": "portal.example.com",
        "path": "/welcome",
        "params": "",
        "query": "token=abc123",
        "fragment": ""
    }
}"""
#   -------------Decoding---------------
class Obj1():
    def __init__(self,sender,client_ip,link):
        self.sender=sender
        self.client_ip=client_ip
        self.link=link
    def __repr__(self):
        return f"obj1(sender={self.sender})  client_ip={self.client_ip}  link={self.link})"

       
class Convert(json.JSONDecoder):
  def __init__(self):
      super().__init__(object_hook=self.object_hook)
  def object_hook(self,obj):
    
    if obj.get("__class") == "EmailMessage":
    
        msg = EmailMessage()

            # Add headers
        for key, value in obj["headers"].items():#whithout '.items()' the output will give jsut key 
            msg[key] = value

            # Add body
        msg.set_content(obj["body"])#set content is methods from EmailMessage  her work is "Put this text inside the email body."

        return msg
    
    
    if obj.get("__class") == "IPv4Address":
    
           return IPv4Address(obj["address"])
            
        
    if obj.get("__class") == "ParseResult":
        return ParseResult(
        obj["scheme"],# We use [] because obj is a dictionary, and we use keys to access its values.
        obj["netloc"],
        obj["path"],
        obj["params"],
        obj["query"],
        obj["fragment"]
        )
    if "sender" in obj:
        return Obj1(obj["sender"],obj["client_ip"],obj["link"])
    
    return obj
done= json.loads(data,cls=Convert)
print(done)

#ُ--------------------Encoding--------------------

class Convert2(json.JSONEncoder):
    def default(self,obj):
      if isinstance(obj, Obj1):
        return {
        "sender": obj.sender,
        "client_ip": obj.client_ip,
        "link": obj.link
         }
      if isinstance(obj,EmailMessage):
        return {
         
        "__class":"EmailMessage",
         "headers": {
            "From": obj["From"], #and here also type dictionary so that we use '[]' not '.'
            "To": obj["To"],
            "Subject":obj["Subject"],
       
        
         },
           "body":obj.get_content().strip()
        }
      if isinstance(obj,IPv4Address):
          return {
                "__class":"IPv4Address",
                 "address": str(obj)
          }
      if isinstance(obj,ParseResult):
          return{
               "__class":"ParseResult",
               "scheme": obj.scheme,#we use '.' to reach atrrbuite because type object
               "netloc":obj.netloc,
              "path":obj.path,
              "params":obj.params,
              "query":obj.query,
              "fragment":obj.fragment
          }
      return super().default(obj)

done_en=json.dumps(done,cls=Convert2,indent=4)
print(done_en)
print(type(done_en))