from google.appengine.ext import db

class SkipUser(db.Model):
  id = db.IntegerProperty()                       #id of the user who has to be skipped        
  screen_name = db.StringProperty()               #screen_name of the user who has to be skipped        