###
# Copyright (c) 2011, Harry Delmolino
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###

import gdata.docs
import gdata.docs.service
import gdata.spreadsheet.service
import re, os
import urllib2
import json
import datetime
import supybot.conf as conf
import supybot.utils as utils
from supybot.commands import *
import supybot.ircmsgs as ircmsgs
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks


class Reddit(callbacks.Plugin):
    """Add the help for "@plugin help Reddit" here
    This should describe *how* to use this plugin."""
    threaded = True
    def __init__(self, irc):
        self.__parent = super(Reddit, self)
        self.__parent.__init__(irc)
        self.google_username = conf.supybot.plugins.Reddit.googleUsername()
        self.google_password = conf.supybot.plugins.Reddit.googlePassword()
        self.Connect(self.google_username,self.google_password)
        self.data = self.Get_data()
        
    def reddit(self, irc, msg, args, username):
        """username

        prints the karma of the user
        """
        data = self.Try_user(username)
        if not data:
            uname = username
        else:
            uname = data["account"]
        reddit_data = urllib2.urlopen('http://www.reddit.com/user/%s/about.json' % uname).read()
        js = json.loads(reddit_data)
        made_utc = js['data']['created_utc']
        link_karma = js['data']['link_karma']
        comment_karma = js['data']['comment_karma']
        now = datetime.date.today()
        then = datetime.date.fromtimestamp(made_utc)
        age = now - then 
        irc.reply("%s has been a redditor for %s days, has %s link karma and %s comment karma." % 
                    (uname, age.days, link_karma, comment_karma))

    reddit = wrap(reddit, ['text'])
    
    def reference(self, irc, msg, args, username):
        """nick

        gets pic of the bike"""
        data = self.Try_user(username)
        if not data:
            irc.reply("%s does not have a reference on file." % username)
        else:
            if data["reference"]:
                irc.reply("%s's reference is %s." % (username,data["reference"]))
            else:
                irc.reply("%s's reference is unknown, dispatching the trained seals now" % username)

    reference = wrap(reference, ['text'])
    
    def location(self, irc, msg, args, username):
        """nick

        gets pic of the bike"""
        data = self.Try_user(username)
        if not data:
            irc.reply("%s does not have a location on file." % username)
        else:
            if data["location"]:
                irc.reply("%s's location is %s." % (username,data["location"]))
            else:
                irc.reply("%s's location is unknown, contacting CIA now." % username)

    location = wrap(location, ['text'])

    def bike(self, irc, msg, args, username):
        """nick

        gets pic of the bike"""
        data = self.Try_user(username)
        if not data:
            irc.reply("%s does not have a bike on file." % username)
        else:
            if data["bikes"]:
                irc.reply("%s has a %s." % (username, data["bikes"]))
            else:
                irc.reply("%s has no bikes. D:" % username)

    bike = wrap(bike, ['text'])
        
    def slap(self, irc, msg, args, offender):
        """
        """
        slap_text = "slaps %s"
        irc.reply(slap_text % offender, prefixNick=False, action=True)
    slap = wrap(slap, ['text'])

    def warn(self, irc, msg, args, offender):
        """
        """
        warn_text = "Please follow the rules in this room. If you are not \
familiar with them, type !rules and I will tell you.  You may be kicked \
next time."
        if offender:
            text = "%s: %s" % (offender, warn_text)
        else:
            text = warn_text
        irc.reply(text, prefixNick=False) #, action=action, msg=msg)
    warn = wrap(warn, [optional('text')])

    def rules(self, irc, msg, args, offender):
        """
        """
        rule_text = "1) Be friendly. 2) Mark links as NSFW if needed. 3) Do not post other \
users' personal information  without their permission."
        if offender:
            text = "%s: %s" % (offender, rule_text)
        else:
            text = rule_text
        irc.reply(text, prefixNick=False) #, action=action, msg=msg)
    
    rules = wrap(rules, [optional('text')])
    
    def Connect(self, username, passwd):
        # Connect to Google
        self.gd_client = gdata.spreadsheet.service.SpreadsheetsService()
        self.gd_client.email = username
        self.gd_client.password = passwd
        self.gd_client.source = 'bikeit-bot'
        self.gd_client.ProgrammaticLogin()
    
    def Get_data(self):
        data = {}
        q = gdata.spreadsheet.service.DocumentQuery()
        q['title'] = "/r/bicycling Directory"
        q['title-exact'] = 'true'
        feed = self.gd_client.GetSpreadsheetsFeed(query=q)
        spreadsheet_id = feed.entry[0].id.text.rsplit('/',1)[1]
        feed = self.gd_client.GetWorksheetsFeed(spreadsheet_id)
        worksheet_id = feed.entry[0].id.text.rsplit('/',1)[1]
        rows = self.gd_client.GetListFeed(spreadsheet_id, worksheet_id)
        for row in rows.entry:
            try:
                data[row.custom['ircnicknamerequired'].text] = {
                'account' : row.custom['redditusernamerequired'].text,
                'bikes' : row.custom['bikes'].text,
                'reference' : row.custom['reference'].text,
                'location' : row.custom['location'].text}
            except Exception, e:
                print e
        return data
    
    def Try_user(self, user, again=True):
        try: 
            data = self.data[user]
        except KeyError:
            if again:
                self.data = self.Get_data()
                return self.Try_user(user, False)
            return False
        else:
            return data

Class = Reddit
# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
