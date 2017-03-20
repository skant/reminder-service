#!/usr/bin/env python

import ConfigParser
import twitter


# get user credentials from config file.
config = ConfigParser.ConfigParser()
config.read('config.cfg')
twitter_username = config.get('TwitterAccount', 'username', 1)
twitter_password = config.get('TwitterAccount', 'password', 1)

print twitter_username
print
print twitter_password
print

#instantiate the API 
api = twitter.Api(twitter_username, twitter_password)

#retrieve the user's timeline
latest_posts = api.GetUserTimeline(twitter_username)
print [s.text for s in latest_posts]

print

#retrieve user's friends
users = api.GetFriends()
print [u.name for u in users]

print

#retrieve the user's direct messages
direct_msgs = api.GetDirectMessages(twitter_username)
print [s.text for s in direct_msgs]