'''In case we have encoded the complex number into JSON Object as list, it will not be possible
 to decoded or convert to pyth complex datatype
 In this example we want to encode and decode complex and datetime
JSON Object below:'''


text={
    "signal": {
        "place": "Uppsala",
        "stamp": {
            "__class": "datetime",
            "y": 2025,
            "month": 4,
            "d": 19,
            "h": 16,
            "minute": 23,
            "s": 51
        },
        "samples": [
            {
                "__class": "complex",
                "real": -2.0,
                "imag": 5.0
            },
            {
                "__class": "complex",
                "real": 3.0,
                "imag": 1.0
            },
            {
                "__class": "complex",
                "real": 2.0,
                "imag": 5.0
            }
        ]
    }
}
class Signal():
    def __init__(self, _place:str, _stamp:datetime, _samples:list[complex]):#for object when we  create it we need to pass the 
        self._place = _place
        self. _stamp = _stamp
       # self._sample= _samples## There was a mistake here. The 's' was missing from 'samples'.
        self._samples =_samples
    @property
    def place(self):#this is a getter method to get the value of the private attribute _place
        return self._place

    @property# # Now we can write signal.place instead of signal._place
    def stamp(self):
        return self._stamp## They also forgot the underscore (_).

    @property
    def samples(self):
        return self._samples

#-------------------Encoding-----------------------

import datetime
import json
class Convert(json.JSONEncoder):
    def default(self, obj):
        
        if isinstance (obj,datetime.datetime):
            return {
                "__class":"datetime",
                "y":obj.year,
                "month":obj.month,
                "d":obj.day,
                "h":obj.hour,
                "minute":obj.minute,
                "s":obj.second
            }
            
        if isinstance(obj,complex):
            return {
                "__class":"complex",
                "real":obj.real,
               "imag":obj.imag
             }
            
        return super().default(obj)#mean if not complex type and datetime type so number or string or list or dictionary will be converted to JSON Object by default method

'''You can see the samples is a list of complex numbers and we have stamps
Use the examples in the previous files (module)  to Decode and Encode the above JSON file
You can see the Python object structure below.
Try to debug your result so you can inspect and see how dictionary is format from the JSON object String 
'''

#---------------------Decoding----------------------------

class Convert2(json.JSONDecoder):
    def __init__(self):
        super().__init__(object_hook=self.object_hook)#object_hook it's for the dictionary that we want to convert it to python object
        #object_hook receives each dictionary created by json.loads() and converts it into the correct Python object if needed.
    def object_hook(self,obj):
        
        if obj.get("__class" )=="complex":#"get mean Look for this key in the dictionary."
            return complex(obj["real"], obj["imag"])
        if obj.get("__class") =="datetime":
           return datetime.datetime(
               
                obj["y"],
                obj["month"],
                obj["d"],
                obj["h"],
                obj["minute"],
                obj["s"]
            )
        return obj
    '''
    The first function initializes the decoder and tells json.loads() to use object_hook.
    The object_hook function receives each dictionary from the JSON and converts it into a 
    Python object (complex or datetime) when needed.
    JSON text
     │
     ▼
json.loads()
     │
     ▼
Creates a dictionary
     │
     ▼
Calls object_hook(dictionary)
     │
     ▼
You decide:
- Return complex?
- Return datetime?
- Return the dictionary?'''

if __name__ == '__main__':
    x = json.dumps(text, cls= Convert)#after we convert the python object to dictanory now we can convert it to text 
    print(x) 
    print(type(x))
    #x become text now will convert it to  object again
    y = json.loads(x, cls=Convert2)
    print(type(y)) # <class, complex)
    print(y) # (2+1j)  the complex value
    sig = y["signal"]#"Take the dictionary inside the key "signal" and store it in the variable sig."
    signal = Signal(
#made object and It calls the constructor: --->def __init__(self, _place, _stamp, _samples):
     sig["place"],
     sig["stamp"],
     sig["samples:"]
     )
    print("\nSignal Object:")
    print(signal.place)
    print(signal.stamp)
    print(signal.samples)