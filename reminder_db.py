from google.appengine.ext import db

class Reminder(db.Model):
  sender_id = db.IntegerProperty()                       #id of the user who requested a reminder
  message = db.StringProperty(multiline=True)            #message send by the user to set a reminder
  message_id = db.IntegerProperty()                      #message id of the message send by the user to set a reminder
  entry_time = db.DateTimeProperty()                     #time when message was sent
  reply_msg = db.StringProperty(multiline=True)          #reply that will be sent to the user as reminder
  reply_time = db.DateTimeProperty()                     #time when a reply will be sent to the user as reminder
  status = db.StringProperty()                           #status of the reminder. P - Pending. R - Reminded. E - Error.
  
