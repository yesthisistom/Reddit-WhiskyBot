import traceback
import praw # simple interface to the reddit API, also handles rate limiting of requests
import time
import sqlite3
import botInfo

'''USER CONFIGURATION'''

#Set Bot Information
USERNAME = botInfo.botName()
PASSWORD = botInfo.botPwd()
USERAGENT = botInfo.botUserAgent()
SUBREDDIT = botInfo.subReddit()

#Strings to search for
SEARCHSTRING = ["@whiskybot"]

SIGNATURE = botInfo.postSignature()
#Automated replies
ADDED_REPLYSTRING = " has been added to the list of users for the weekly roundup" + SIGNATURE
USEREXISTS_REPLYSTRING = " has previously been added to the list of users" + SIGNATURE
REMOVED_REPLYSTRING = " has been removed from the list of users for the weekly roundup" + SIGNATURE
EXPLANATION_REPLYSTRING = """ Valid calls are:

* @whiskybot add
* @whiskybot remove

The first adds your username to the weekly roundup, the second removes you""" + SIGNATURE

#Variables
MAXPOSTS = 100
WAITS = 120 #only check every 2 minutes, this sub doesn't go too crazy


##Load SQL Database, and make sure the tables are created
sql = sqlite3.connect('sql.db')
print('LoadedSQL Database')
cur = sql.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS oldposts(ID TEXT)')
cur.execute('CREATE TABLE IF NOT EXISTS users(USER TEXT, SUBREDDIT TEXT)')

print('Loaded Completed table')

sql.commit()

r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD) 

def scanSub():
	print('Searching '+ SUBREDDIT + '.')
	subreddit = r.get_subreddit(SUBREDDIT)
	posts = subreddit.get_comments(limit=MAXPOSTS)
	for post in posts:
		pid = post.id
		try:
			pauthor = post.author.name
			cur.execute('SELECT * FROM oldposts WHERE ID=?', [pid])
			if not cur.fetchone():
				cur.execute('INSERT INTO oldposts VALUES(?)', [pid])
				pbody = post.body.lower()
				if any(key.lower() in pbody for key in SEARCHSTRING):
					if pauthor.lower() != USERNAME.lower():
						if "add" in pbody:
							#Check to make sure they're not already in there
							cur.execute('SELECT * FROM users WHERE USER=?', [pauthor])
							if not cur.fetchone():
								print('Replying to add request ' + pid + ' by ' + pauthor)
								cur.execute('INSERT INTO users VALUES(?,?)', [pauthor, SUBREDDIT])
								post.reply("User /u/" + pauthor + ADDED_REPLYSTRING)
							else: 
								post.reply("User /u/" + pauthor + USEREXISTS_REPLYSTRING)
							
						elif "remove" in pbody:
							print('Replying to remove request ' + pid + ' by ' + pauthor)
							cur.execute('DELETE FROM users WHERE USER=?', [pauthor])
							post.reply("User /u/" + pauthor + REMOVED_REPLYSTRING)
						else:
							print('Replying to blank request ' + pid + ' by ' + pauthor)
							post.reply(EXPLANATION_REPLYSTRING)
					else:
						print('Will not reply to self')
		except AttributeError:
			pauthor = '[DELETED]'
	sql.commit()


while True:
	try:
		scanSub()
	except Exception as e:
		traceback.print_exc()
	print('Running again in ' + str(WAITS) + ' seconds \n')
	sql.commit()
	time.sleep(WAITS)

	