'''
Created on Jun 1, 2009

@author: Shashi Kant
'''

import re

Weekdays      = [ u'monday', u'tuesday', u'wednesday',
                   u'thursday', u'friday', u'saturday', u'sunday',
                 ]
shortWeekdays = [ u'mon', u'tues', u'wed',
                   u'thu', u'fri', u'sat', u'sun',
                 ]
Months        = [ u'january', u'february', u'march',
                   u'april',   u'may',      u'june',
                   u'july',    u'august',   u'september',
                   u'october', u'november', u'december',
                 ]
shortMonths   = [ u'jan', u'feb', u'mar',
                   u'apr', u'may', u'jun',
                   u'jul', u'aug', u'sep',
                   u'oct', u'nov', u'dec',
                 ]

DAYS ="(?P<days>("+ "|".join(Weekdays) + "|" + "|".join(shortWeekdays) +"))"
HASH = "#"
HASHES= "###############################"
def parseMsg(text): 
   text = "   " + text + "   " # 3 spaces
   text = text.lower()
   day_regex_begin = r'((\s.*)|([0-9](st|nd|rd|th))|(\d.*))'
   day_regex_end   = r'([^a-z])' 
   
   days_regex = day_regex_begin + DAYS + day_regex_end
   print days_regex
   
   p = re.compile(days_regex)
   print text
   for s in re.finditer(DAYS, text):
      a = s.start()
      b = s.end()
      #print "Text: "+ text[a-2:b+2]
      if p.search(text[a-3:b+3]) == None :
         #print text[a:]
         #print text[:b]
         print a
         print b
         print text[a:b]
         text = text[:a] + HASHES[0:b-a] + text[b:]
         #text = text[a:] + HASHES[0:b-a] + text[:b]
            
   print text
   

   


if __name__ == '__main__':
    text = "Wedding  wed iir  teuder frider on 23 Wed"
    parseMsg(text)