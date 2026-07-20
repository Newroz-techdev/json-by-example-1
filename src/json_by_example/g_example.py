import json
from datetime import date,timedelta,timezone
import datetime
#concept of datetime
#date: It is  represented by year,month,day
# timedelta: If the date is April 5 and we add timedelta(days=3),
# the new date becomes April 8.
#April 27  +  3 days  =  April 30
  # date      timedelta      date
  
#What is UTC?
# the whole world agrees on one official clock.
#That clock is called UTC.
#Timezones:A time zone is a region that uses the same local time.
data = """{
    "report": {
        "created": {
            "__class": "date",
            "y": 2025,
            "month": 4,
            "d": 27
        },
        "duration": {
            "__class": "timedelta",
            "days": 2,
            "seconds": 3600,
            "microseconds": 4
        },
        "timezone": {
            "__class": "timezone",
            "offset": 2
        }
    }
}"""
#-----------------Decoding------------------
class Obj1():
    def __init__(self,report):
        self.report=report
    def __repr__(self):
            return f"Obj1(report={self.report})"

class Obj2():
    def __init__(self,created,duration,timezone):
        self.created=created
        self.duration=duration
        self.timezone=timezone
    def __repr__(self):
            return (f"Obj2(created={self.created}, "
                f"duration={self.duration}, "
                f"timezone={self.timezone})")
        

class Convert(json.JSONDecoder):
    def __init__(self):
        super().__init__(object_hook=self.object_hook)
    def object_hook(self,obj):
         
        if obj.get("__class") == "date":
            return date(
                
                obj["y"],
                obj["month"],
                obj["d"],
            )
       
        if obj.get("__class") =="timedelta":
            
            return timedelta(
               
                obj["microseconds"],
                obj["days"],
                obj["seconds"]
            )
        if obj.get("__class") =="timezone":
                return timezone(
               
                timedelta(hours=obj["offset"])#we use timedelta to know how many hours add to timezone region
               
            )
        if "created" in obj:
            return Obj2(obj["created"],obj["duration"],obj["timezone"])
        if "report" in obj:
            return Obj1(obj["report"])
        return obj
conev_obj=json.loads(data,cls=Convert)
print(conev_obj) 
print(type(conev_obj))




#---------------Encoding------------------


from datetime import date, timedelta, timezone


data = """{
    "report": {
        "created": {
            "__class": "date",
            "y": 2025,
            "month": 4,
            "d": 27
        },
        "duration": {
            "__class": "timedelta",
            "days": 2,
            "seconds": 3600,
            "microseconds": 4
        },
        "timezone": {
            "__class": "timezone",
            "offset": 2
        }
    }
}"""



#----------------Encoding-----------------
class Convert2(json.JSONEncoder):
    def default(self,obj):
        if isinstance(obj,Obj1):
            return{
                "report":obj.report
            }
        if isinstance(obj, Obj2):
          return {
        "created": obj.created,
        "duration": obj.duration,
        "timezone": obj.timezone
          }
        if isinstance(obj,date):
          if isinstance(obj, date):
             return {
               "__class": "date",
               "y": obj.year,
               "month": obj.month,
               "d": obj.day
    }
            
        if isinstance(obj,timedelta):
           return{ 
            "__class": "timedelta",
            "days": obj.days,
            "seconds": obj.seconds,
            "microseconds": obj.microseconds
           }
        if isinstance(obj, timezone):
         return {
           "__class": "timezone",
           "offset": obj.utcoffset(None).total_seconds() // 3600
        }
conv_text=json.dumps(conev_obj,cls=Convert2)
print(conv_text)
print(type(conv_text))
            
        
