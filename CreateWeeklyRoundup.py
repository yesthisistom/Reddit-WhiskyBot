#TODO: Create a quiet mode
#Note: This can be run in Roundup mode or swap mode.  Defaults to roundup if no arguments
#	eg; py CreateWeeklyRoundup.py roundup
#		py CreateWeeklyRoundup.py swap

import traceback
import praw #Reddit Interface
import datetime
import time
import botInfo
import sqlite3
import sys

#Set Bot Information
USERNAME = botInfo.botName()
PASSWORD = botInfo.botPwd()
USERAGENT = botInfo.botUserAgent()
SUBREDDIT = botInfo.subReddit()

#Turn Debug and submit on or off
DEBUG = False
SUBMIT = True

#This determines whether or not we're doing a roundup or scotch swap post
ROUNDUP=True;
###Read the arguments
if len(sys.argv) > 0:
	for arg in sys.argv:
		if "swap" == arg.lower():
			ROUNDUP = False
			
			
if DEBUG:
	if ROUNDUP:
		print ("Running in roundup mode")
	else:
		print ("Running in swap mode")
	


#Log into reddit
r = praw.Reddit(USERAGENT)
r.login(USERNAME, PASSWORD)

#Set a variety of global variables
MAXPOSTS = 50

SECONDS_IN_A_WEEK = 604800
SECONDS_IN_12_HOURS = 43200
DATE=datetime.date.today()
EPOCHSECONDS = int(time.time())
ECOCHSECONDS_LASTWEEK = EPOCHSECONDS - SECONDS_IN_A_WEEK

REVIEWPHRASES = ["review", "reviews"]

#Define the arrays that will hold user posts
SCOTCH_REVIEWS=[]
BOURBON_REVIEWS=[]
WORLDWHISKY_REVIEWS=[]
WHISKYPORN_POSTS=[]

#For a ScotchSwap Post
SCOTCHSWAP_POSTS=[]
SCOTCHSWAP_ISO=[]
SCOTCHSWAP_FT=[]


##Load SQL Database, and make sure the tables are created
sql = sqlite3.connect('sql.db')
print('LoadedSQL Database')
cur = sql.cursor()

cur.execute('CREATE TABLE IF NOT EXISTS oldposts(ID TEXT)')
cur.execute('CREATE TABLE IF NOT EXISTS users(USER TEXT, SUBREDDIT TEXT)')

sql.commit()

#####################
##Function for getting a users whisky posts
#####################
def getUserPosts(inputUsername): # Get posts from a user, break them down by subreddit
	user = r.get_redditor(inputUsername)
	postList = user.get_submitted(sort='new',time='week',limit=MAXPOSTS)
	for post in postList:
		#if DEBUG:
		#	print (post.subreddit.display_name)
		
		#Check to make sure it was posted in the last week
		if ECOCHSECONDS_LASTWEEK <= post.created + SECONDS_IN_12_HOURS:
			#Check for the words Review or Reviews
			if any(key.lower() in post.title.lower() for key in REVIEWPHRASES):
				if post.subreddit.display_name.lower() == 'scotch':
					if DEBUG:
						print ('Adding to Scotch')
					SCOTCH_REVIEWS.append(post)
				
				if post.subreddit.display_name.lower() == 'bourbon':
					if DEBUG:
						print ('Adding to Bourbon')
					BOURBON_REVIEWS.append(post)
					
				if post.subreddit.display_name.lower() == 'worldwhisky':
					if DEBUG:
						print ('Adding to World Whisky')
					WORLDWHISKY_REVIEWS.append(post)
					
			#Check for ScotchSwap Posts, separate them into appropriate categories
			if post.subreddit.display_name.lower() == 'scotchswap':
				if DEBUG:
					print ('Adding to Scotch Swap')
				if "ft:" in post.title.lower() :
					SCOTCHSWAP_FT.append(post)
				elif "iso:" in post.title.lower():
					SCOTCHSWAP_ISO.append(post)
				else:
					SCOTCHSWAP_POSTS.append(post)
				
			#Check for WhiskyPorn Posts
			if post.subreddit.display_name.lower() == 'whiskyporn':
				if DEBUG:
					print ('Adding to Whisky Porn')
				WHISKYPORN_POSTS.append(post)
				
	sql.commit()

####################
##Function for adding text to our weekly post
####################			
def addToPost(POST_LIST, TITLE, SUBREDDIT):
	if len(POST_LIST) > 0:
		toReturnText=""
		if len(TITLE) > 0:
			toReturnText="""

**[%s](http://reddit.com/r/%s)**
  
""" % (TITLE, SUBREDDIT)

		for whiskypost in POST_LIST:
			
			#Get the url we want to use
			urlLink = whiskypost.short_link
			if len(TITLE) == 0: #then we're whiskyporn (yes, this is a shitty hack)
				urlLink = whiskypost.url

			#Add to the resturn text
			toReturnText += """* /u/%s - %s ([link](%s)) 
""" % (whiskypost.author.name, whiskypost.title, urlLink)
		
		#once we've looped through, add a line break
		toReturnText += """
    
&nbsp;  
  
"""  
		return toReturnText
		

##########################
#Main function calls
##########################

try:
	##################
	##Loop over our users
		
	USERLIST = cur.execute('SELECT USER FROM users WHERE SUBREDDIT=?', [SUBREDDIT])
	for username in USERLIST:
		if DEBUG:
			print ('Calling getUserPosts for: ' + str(username))
		getUserPosts(username)
		
	########################
	##Initialize the post title and text
	PostTitle = "Whisky Weekly Roundup: " + str(DATE.month) + "/" + str(DATE.day) + "/" + str(DATE.year)
	PostText = """
Welcome to /r/dcwhisky's auto-generated Weekly Review Roundup for the week of %s/%s/%s

&nbsp;  

""" % (str(DATE.month), str(DATE.day), str(DATE.year))

	if not ROUNDUP:
		PostTitle = "DCWhisky's ScotchSwap Roundup and ISO/FT Thread: " + str(DATE.month) + "/" + str(DATE.day) + "/" + str(DATE.year)
		PostText = """
Welcome to /r/dcwhisky's auto-generated ScotchSwap Roundup and ISO/FT Thread for %s/%s/%s

&nbsp;  

""" % (str(DATE.month), str(DATE.day), str(DATE.year))
	
		
	########################
	##Create the content for our post
	
	if ROUNDUP:
		if len(SCOTCH_REVIEWS + BOURBON_REVIEWS + WORLDWHISKY_REVIEWS) > 0:
			PostText += """**Reviews Posted by DCWhisky Users**
	  
===
---
	  
"""
		if len(SCOTCH_REVIEWS) > 0:
			PostText += addToPost(SCOTCH_REVIEWS, 'Scotch Reviews', 'Scotch')
		if len(BOURBON_REVIEWS) > 0:
			PostText += addToPost(BOURBON_REVIEWS, 'Bourbon Reviews', 'Bourbon')
		if len(WORLDWHISKY_REVIEWS) > 0:
			PostText += addToPost(WORLDWHISKY_REVIEWS, 'WorldWhisky Reviews', 'WorldWhisky')
		if len(WHISKYPORN_POSTS) > 0:
			PostText += """**DCWhisky's Whisky Porn**
  
===
---
  
"""   
			PostText += addToPost(WHISKYPORN_POSTS, '', '')
		
		
		
	#Scotch Swap
	else:
		if len(SCOTCHSWAP_POSTS + SCOTCHSWAP_ISO + SCOTCHSWAP_FT) > 0:
			PostText += """**ScotchSwap Posts by DCWhisky Users**
  
===
---
  
"""	
		if len(SCOTCHSWAP_POSTS) > 0:
			PostText += addToPost(SCOTCHSWAP_POSTS, 'ScotchSwap Posts', 'ScotchSwap')
		if len(SCOTCHSWAP_ISO) > 0 or len(SCOTCHSWAP_FT) > 0:
			PostText += addToPost(SCOTCHSWAP_ISO + SCOTCHSWAP_FT, 'ScotchSwap FT/ISO Posts', 'ScotchSwap')
			
		
	
		
	#add the file signature
	PostText += botInfo.postSignature()
		

	if DEBUG:
		print (PostTitle)
		print (PostText)

	if SUBMIT:
		SubmitResult = r.submit(SUBREDDIT, PostTitle, text=PostText)
		PostURL = SubmitResult.url
		print (PostURL)
		
	sql.commit()
		
except Exception as e:
	traceback.print_exc()