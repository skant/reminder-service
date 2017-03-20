#!/usr/bin/env python
from datetime import datetime, timedelta
from google.appengine.api.urlfetch_errors import DownloadError
from google.appengine.ext import db, webapp
from reminder_db import Reminder
from skip_user_db import SkipUser
from sets import Set
from urllib2 import HTTPError
import ConfigParser
import logging
import parsedatetime.parsedatetime as pdt
import parsedatetime.parsedatetime_consts as pdc
import re
import string
import time
import twitter
import wsgiref.handlers

# Global username and password.
pdcConst = pdc.Constants()
config = ConfigParser.ConfigParser()
config.read('config.cfg')
twitter_username = config.get('TwitterAccount', 'username', 1)
twitter_password = config.get('TwitterAccount', 'password', 1)
api = twitter.Api(twitter_username, twitter_password)

_debug = False

PARSE_ERROR_MESSAGE = "Uh Oh! I couldn't understand what you just said to me. Please have a look at http://bit.ly/laterr to find out how to send reminders to me."
FIRST_TIME_USER_MESSAGE = "Howdy. Thanks for trying me out. Take a look at http://bit.ly/laterr to use me more effectively. Thanks."
TIMEZONE_NOT_SET_ERROR = "Oh no. You forgot to set your Twitter timezone setting. I need that to send your reminders correctly. Go set it here http://bit.ly/SetTzone"
REMINDER_SET_AT_FORMAT = "%I:%M%p - %A, %d %B %Y"
TOTAL_DIRECT_MSG_PULL_COUNT = 200 
REPLY_PREFIX = "REMINDER:" 
STATUS_REPLIED = "R"
STATUS_NEW = "N"
STATUS_ERROR = "E"
SUCCESS = 1
ERROR = -1

INDIA_TIME_NOW = str((datetime.utcnow() + timedelta(seconds=19800)).strftime("%d/%m/%Y %H:%M:%S")) + " -"


class MainHandler(webapp.RequestHandler):

 def get(self):
    if _debug:
       print 'Content-Type: text/plain'
       print ''
    
    autoFollow(self)

    populateDbWithLatestDirectMsgs(self)

    PostReminder(self)


   #UTCtest(self)

def populateDbWithLatestDirectMsgs(self):
   query = Reminder.all()
   latest_reminder = query.order('-message_id').get()
   if query.count() == 0:
      latest_message_id = None
   else:   
      latest_message_id = latest_reminder.message_id

   #self.response.out.write("<br><br> Id:" + str(latest_message_id))
   latest_direct_msgs = MyGetDirectMessages(since_id=latest_message_id, count=TOTAL_DIRECT_MSG_PULL_COUNT)
   
   if latest_direct_msgs == ERROR: # using the same variable for msgs and error code :)
      return
   
   if len(latest_direct_msgs) > 0:
      logging.info(INDIA_TIME_NOW + " PopulateDB: Found new: " + str(len(latest_direct_msgs)) + " direct messages")
   else:
      logging.info(INDIA_TIME_NOW + " PopulateDB: Now new direct messages found")
      return

   for msg in latest_direct_msgs:
      reminder = Reminder()
      reminder.sender_id = msg.sender_id
      created_at_in_seconds = msg.created_at_in_seconds
      #logging.info(msg.sender_screen_name + " Created in secs "+ str(created_at_in_seconds))
      reminder.entry_time = datetime.utcfromtimestamp(created_at_in_seconds)
      if _debug:
         print msg.text
      postMessage , datetime_diff, sourceLocal_time , returnCode = getMsgNTime(msg.text, reminder.entry_time, msg.sender_id)
      
      if returnCode == SUCCESS :
         reminder.status = STATUS_NEW
         reply_time =  reminder.entry_time +  datetime_diff
      else :
         reminder.status = STATUS_ERROR
         reply_time =  reminder.entry_time
      
      reminder.message = msg.text
      reminder.message_id = msg.id
      reminder.reply_msg = postMessage
      
      reminder.reply_time = reply_time
      logging.info(INDIA_TIME_NOW + " PopulateDB: Persisting to DB msg from >>> " + msg.sender_screen_name + " >>> Message >>> " + str(msg.text))
      reminder.put()
      if returnCode == SUCCESS and datetime_diff > timedelta(minutes=5):
         dt_temp = sourceLocal_time + datetime_diff
         formatted_date = dt_temp.strftime(REMINDER_SET_AT_FORMAT)
         MyPostDirectMessage(user=msg.sender_id, text="Okay, I got that. I will remind you at " + str(formatted_date))

def PostReminder(self):
   query = Reminder.gql("WHERE status='"+ STATUS_NEW +"' AND  reply_time < :time" , time=datetime.utcnow()) 
   offset = 0
   results = query.fetch(200, offset)
   while len(results) > 0:
      for result in results:
         logging.info(INDIA_TIME_NOW + " PostReminder: " + str(result.sender_id) + " >>> " + str(result.reply_msg))
         return_code =  MyPostDirectMessage(user=result.sender_id, text=result.reply_msg[0:140])
         
         if return_code == ERROR :
            continue         # It will simply skip from persisting to DB. Reminder will be re-tried at next cron job
         
         result.status = STATUS_REPLIED
         result.put()
         
      logging.info(INDIA_TIME_NOW + " PostReminder: Sent: " + str(len(results)) + " new reminders");
      offset = offset + len(results);
      results = query.fetch(len(results), offset)


def autoFollow(self):
   # Get the list of friends.
   following = MyGetFriends()
   # Create a set consisting of the ids of your friends.
   friendNames = Set()
   for friend in following:
      friendNames.add(friend.id)

   # For every follower that isn't already one of your friends: ...
   query = SkipUser.all()
   followers = MyGetFollowers()
   for follower in followers:
      if (not follower.id in friendNames ):
         if query.filter('id =', follower.id).count() > 0:
            logging.info(INDIA_TIME_NOW + " Skipping follow: >> " + follower.screen_name +" << . Friendship request pending.")
            continue
         
         # ... add that follower as a friend.
         return_code = MyCreateFriendship(follower.id)
         
         if return_code == SUCCESS:
            MyPostDirectMessage(user=follower.id, text=FIRST_TIME_USER_MESSAGE)
            logging.info(INDIA_TIME_NOW + " AutoFollow: Adding new friend: " + follower.screen_name + " " + str(follower.id))
         else :
            logging.info(INDIA_TIME_NOW + follower.screen_name + " has blocked friendship request. Adding to skip list")
            skipUser = SkipUser()
            skipUser.id = follower.id
            skipUser.screen_name = follower.screen_name
            skipUser.put()
  
def UTCtest(self):
   latest_direct_msgs = MyGetDirectMessages(since_id=None, count=200)
   for msg in latest_direct_msgs:
      user = MyGetUser(msg.sender_id)
      if _debug:
         print user.screen_name
         print str(user.utc_offset) + " = " + str(user.utc_offset / 3600.0) + " hrs"
      # To convert from user's offset value to UTC format
      utc_time_no_offset = datetime.utcfromtimestamp(msg.created_at_in_seconds)
      utc_time_with_offset = utc_time_no_offset + timedelta(seconds= -user.utc_offset)
      #                                         important             ^
      if _debug:
         print "Twitter time: " + str(utc_time_no_offset)
         print "UTC time    : " + str(utc_time_with_offset)
         print user.time_zone
         print

def getMsgNTime(directMsg, sourceTime, sender_id):
   spaces_regex = re.compile( r'\s+')
   strippedDirectMsg = spaces_regex.sub(" ", str.strip(str(directMsg)))
      
   pdtObj = pdt.Calendar(pdcConst)
   
   user = MyGetUser(sender_id)
   if user.utc_offset != None :
      logging.info(INDIA_TIME_NOW + " "+ user.screen_name + " offset " + str(user.utc_offset))
      sourceTime_local = sourceTime + timedelta(seconds=user.utc_offset)
      # removing microseconds part of the time as it is causing discrepancy
      sourceTime_local = sourceTime_local - timedelta(microseconds=sourceTime_local.microsecond)
      reminderTime,  returnCode = pdtObj.parse(strippedDirectMsg, sourceTime_local)
      if _debug:
         print "Source time = " + str(sourceTime)
         print "Source time local = " + str(sourceTime_local)
         print "Reminder Time = " + str(reminderTime)
   else :
      #timezone not set for the user
      postErrorMessage(sender_id, TIMEZONE_NOT_SET_ERROR)
      return(TIMEZONE_NOT_SET_ERROR, None, sourceTime, ERROR)      

   
   if returnCode !=0 :
      datetime_diff = convertToDateTime(reminderTime) - sourceTime_local
      if _debug:
         print "DatTime Diff =  " + str(datetime_diff)
      # Fix for issue http://code.google.com/p/reminder-service/issues/detail?id=1&can=1
      if datetime_diff < timedelta() :
         days_diff = - datetime_diff.days
         datetime_diff = timedelta(days=days_diff) + datetime_diff 
      # End Fix
      
      reminderMsg = REPLY_PREFIX + strippedDirectMsg
      return(reminderMsg , datetime_diff, sourceTime_local ,SUCCESS)
   else :
      postErrorMessage(sender_id, PARSE_ERROR_MESSAGE)
      return(PARSE_ERROR_MESSAGE , None, sourceTime ,ERROR)

def convertToDateTime(dateTimeList):
   date_list = dateTimeList[0:3]
   time_list = dateTimeList[3:6]

   d = []
   for item in date_list:
      d.append(str(item))
   
   t = []
   for item in time_list:
      t.append(str(item))
   
   date = "/".join(d);
   time = ":".join(t)
   
   dt = datetime.strptime(date + " " +time, "%Y/%m/%d %H:%M:%S")
   
   return dt

def postErrorMessage(sender_id, msg ):
   MyPostDirectMessage(user=sender_id, text=msg)
   if msg == PARSE_ERROR_MESSAGE :
      logging.info(INDIA_TIME_NOW + " PostErrorMessage: Error occured in parsing for "+str(sender_id)+". Messaged User")
   elif msg == TIMEZONE_NOT_SET_ERROR :
      logging.info(INDIA_TIME_NOW + " PostErrorMessage: Timezone not set for "+str(sender_id)+". Messaged User")

      
def MyGetDirectMessages(since_id, count):
   retry_count = 3 
   i = 0
   while i < retry_count : 
      try:
         if i > 0 :
            logging.info(INDIA_TIME_NOW + " RETRY: "+str(i)+". GetDirectMessages: Pulling msgs from since: "+str(since_id))
          
         msgs = api.GetDirectMessages(since_id=since_id, count=count)
         return msgs
      except HTTPError, e:
         i = i+1
         continue
      except DownloadError, e:
         i = i+1
         continue
      except twitter.TwitterError, e:
         i = i+1
         continue
   logging.critical(INDIA_TIME_NOW + " Failed to GetDirectMessages")
   return ERROR
   
def MyPostDirectMessage(user=None, text=None):
   retry_count = 3 
   i = 0
   while i < retry_count : 
      try:
         if i > 0 :
            logging.info(INDIA_TIME_NOW + " RETRY: "+str(i)+". PostDirectMessage: Trying to send message>>> "+str(text)+" >>>to>>> "+ str(user))
            
         status = api.PostDirectMessage(user=user, text=text)
         return SUCCESS

      except HTTPError, e:
         i = i+1
         continue
      except DownloadError, e:
         i = i+1
         continue
      except twitter.TwitterError, e:
         i = i+1
         continue
      
   logging.critical(INDIA_TIME_NOW + " Failed to PostDirectMessage for " +str(user) +" : "+ str(text))
   return ERROR
   
def MyGetUser(id):
   retry_count = 3 
   i = 0
   while i < retry_count : 
      try:
         if i > 0 :
            logging.info(INDIA_TIME_NOW + " RETRY: "+str(i)+". GetUser: Trying to get user >>> "+str(id))
            
         user = api.GetUser(id)
         
        
         return user

      except HTTPError, e:
         i = i+1
         continue
      except DownloadError, e:
         i = i+1
         continue
      except twitter.TwitterError, e:
         i = i+1
         continue
   logging.critical(INDIA_TIME_NOW + " Failed to Get User for " +str(id) )
   
def MyGetFriends() :
   retry_count = 3 
   i = 0
   while i < retry_count : 
      try:
         if i > 0 :
            logging.info(INDIA_TIME_NOW + " RETRY: "+str(i)+". Pulling list of friends ")
            
         friends = api.GetFriends()
         return friends;

      except HTTPError, e:
         i = i+1
         continue
      except DownloadError, e:
         i = i+1
         continue
      except twitter.TwitterError, e:
         i = i+1
         continue
   logging.critical(INDIA_TIME_NOW + " Failed to get list of friends")

def MyGetFollowers():
   retry_count = 3 
   i = 0
   while i < retry_count : 
      try:
         if i > 0 :
            logging.info("RETRY: "+str(i)+". Pulling list of followers ")
            
         followers = api.GetFollowers()
         return followers;

      except HTTPError, e:
         i = i+1
         continue
      except DownloadError, e:
         i = i+1
         continue
      except twitter.TwitterError, e:
         i = i+1
         continue
   logging.critical(INDIA_TIME_NOW + " Failed to get list of followers")
   
def MyCreateFriendship(friend_id):
   retry_count = 5 
   i = 0
   while i < retry_count : 
      try:
         if i > 0 :
            logging.info(INDIA_TIME_NOW + " RETRY: "+str(i)+". Trying to create Friendship ")
            
         friend = api.CreateFriendship(friend_id)
         return SUCCESS

      except HTTPError, e:
         i = i+1
         continue
      except DownloadError, e:
         i = i+1
         continue
      except twitter.TwitterError, e:
         i = i+1
         continue
      
      logging.critical(INDIA_TIME_NOW + "Failed to create Friendship")
      return ERROR
   
def main():
  application = webapp.WSGIApplication([('/', MainHandler)],
                                       debug=True)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()
