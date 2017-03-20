"""
Basic examples of how to use parsedatetime
"""

__license__ = """"""

import parsedatetime.parsedatetime as pdt
import parsedatetime.parsedatetime_consts as pdc
import string
import re
from datetime import datetime, timedelta
# create an instance of Constants class so we can override some of the defaults

c = pdc.Constants()

c.BirthdayEpoch = 80    # BirthdayEpoch controls how parsedatetime
                        # handles two digit years.  If the parsed
                        # value is less than this value then the year
                        # is set to 2000 + the value, otherwise
                        # it's set to 1900 + the value

# create an instance of the Calendar class and pass in our Constants
# object instead of letting it create a default

p = pdt.Calendar(c)

# parse "tomorrow" and return the result
directMsg = "  pay airtel bill in                   indiranagar in 1 days  "
spaces_regex = re.compile( r'\s+')
strippedDirectMsg = spaces_regex.sub(" ", str.strip(directMsg))
parts = string.rsplit(strippedDirectMsg , "in" ,1)
reminderText = parts[0]
reminderAt = parts[1]

#reminderTime = p.parse(reminderAt)
#print reminderTime


sTime = datetime.utcnow() + timedelta(seconds=19800)
print  sTime
text1 = "end of day"
result,  rcode  = p.parse(text1, sTime)
print text1

date_list = result[0:3]
time_list = result[3:6]
print date_list
print time_list

d = []
for item in date_list:
   d.append(str(item))

t = []
for item in time_list:
   t.append(str(item))

date = "/".join(d);
time = ":".join(t)


dt = datetime.strptime(date + " " +time, "%Y/%m/%d %H:%M:%S")

print dt


# parseDate() is a helper function that bypasses all of the
# natural language stuff and just tries to parse basic dates
# but using the locale information

result = p.parseDate("4/4/79")
#print "\n\n4/4/80";
#print result;

# parseDateText() is a helper function that tries to parse
# long-form dates using the locale information

result = p.parseDateText("March 5th, 1980")
#print "\n\nMarch 5th, 1980";
#print result;