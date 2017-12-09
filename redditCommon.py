import praw
import sqlite3
import itertools

from datetime import datetime

import botInfo

#########################
## Connects to reddit using praw, with the values contained in the botInfo library
##  Tests the connection.  If it fails, returns None, otherwise returns the reddit connection
#########################
def reddit_login():

    reddit = praw.Reddit(client_id=botInfo.getClientID(),
                 client_secret=botInfo.getClientSecret(),
                 password=botInfo.getUserPWD(),
                 user_agent=botInfo.getUserAgent(),
                 username=botInfo.getUserID())
    
    try:
        reddit.user.me()
    except:
        print ("Failed to log in")
        return None
    
    return reddit
    
    
################
##  Reads the sqlite3 db "sql.db" contained in the same folder.  
##   If the oldposts and users tables do not exist, it will create them
##   Returns the handle to the sql db
################
def read_sql():

    ##Load SQL Database, and make sure the tables are created
    sql = sqlite3.connect('sql.db')
    print('LoadedSQL Database')
    cur = sql.cursor()

    cur.execute('CREATE TABLE IF NOT EXISTS oldposts(ID TEXT)')
    cur.execute('CREATE TABLE IF NOT EXISTS users(USER TEXT, SUBREDDIT TEXT)')

    print('Loaded Completed table')

    sql.commit()
    
    return sql
    
#####################
## Gets a given users post for a time period
##  Inputs: Reddit connection object, desired username (str), and the minimum acceptable date for posts (datetime)
##  Return: dictionary mapping sub or content type to 
#####################

def getUserPosts(reddit, username, min_date): # Get posts from a user, break them down by subreddit
    
    max_posts = 100
    
    review_phrases = ["review", "reviews"]
    
    postList = reddit.redditor(username).submissions.new(limit=max_posts)
    
    post_dict = {}
    review_subs = ["scotch", "bourbon", "worldwhisky"]
    other_subs = ["scotchswap", "whiskyporn", "whisky"]

    for sub in itertools.chain(review_subs, other_subs):
        post_dict[sub] = []
    post_dict["discussion"] = []
    
    #Iterate over posts
    for post in postList:

        #Check to make sure it was posted after the request date
        post_date = datetime.fromtimestamp(post.created)
    
        if post_date >= min_date:
            
            # Get the subreddit it was posted to
            post_sub = post.subreddit.display_name.lower()
            
            # Check subreddit for review subs
            if  post_sub in review_subs:
                if any(key.lower() in post.title.lower() for key in review_phrases): 
                    post_dict[post_sub].append(post)
                else:
                    post_dict["discussion"].append(post)
                    
            #Check for ScotchSwap Posts, separate them into appropriate categories
            elif post_sub in other_subs:
                
                if (post_sub == "whisky"):
                    post_dict["discussion"].append(post)
                
                else:
                    post_dict[post_sub].append(post)
    
    return post_dict