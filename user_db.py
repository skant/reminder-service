from google.appengine.ext import db

class User(db.Model):
               id = db.IntegerProperty()  
               name =  db.StringProperty()  
               screen_name = db.StringProperty()  
               location = db.StringProperty()  
               description = db.StringProperty()  
               utc_offset  = db.IntegerProperty()  
               time_zone = db.StringProperty()  
