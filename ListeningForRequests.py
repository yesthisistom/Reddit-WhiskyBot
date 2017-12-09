import sys
import time

import botInfo
import sqlite3

import redditCommon


########################
## Takes a reddit connection object, the desired subreddit, and an sql cursor
##  Loops through the most recent posts in the subreddit, looking for key words
##  Adds the ID for each comment to the sql DB.  If it already exists, skips it
##  If a comment that hasn't been processed previously contains 
########################
def scan_sub(reddit, subreddit_name, cur):
    
    search_strings = ["@whiskybot"]
    
    signature = botInfo.postSignature()
    #Automated replies
    add_replystr = " has been added to the list of users for roundup posts" + signature
    exists_replystr = " has previously been added to the list of users" + signature
    rmv_replystr = " has been removed from the list of users for roundup posts" + signature
    
    help_replystr = """ Valid calls are:

    * @whiskybot add
    * @whiskybot remove

    The first adds your username to the weekly roundup, the second removes you""" + signature

    #Variables
    max_posts = 500
    
    print('Searching '+ subreddit_name)
    subreddit = reddit.subreddit(subreddit_name)
    posts = subreddit.comments(limit=max_posts)
    for post in posts:
        pid = post.id
        try:
            pauthor = post.author.name
            cur.execute('SELECT * FROM oldposts WHERE ID=?', [pid])
            if not cur.fetchone():
                cur.execute('INSERT INTO oldposts VALUES(?)', [pid])
                pbody = post.body.lower()
                if any(key.lower() in pbody for key in search_strings):
                    if pauthor.lower() != botInfo.getUserID().lower():
                        if "add" in pbody:
                            #Check to make sure they're not already in there
                            cur.execute('SELECT * FROM users WHERE USER=?', [pauthor])
                            if not cur.fetchone():
                                print('Replying to add request ' + pid + ' by ' + pauthor)
                                cur.execute('INSERT INTO users VALUES(?,?)', [pauthor, subreddit_name])
                                post.reply("User /u/" + pauthor + add_replystr)
                            else: 
                                post.reply("User /u/" + pauthor + exists_replystr)
                            
                        elif "remove" in pbody:
                            print('Replying to remove request ' + pid + ' by ' + pauthor)
                            cur.execute('DELETE FROM users WHERE USER=?', [pauthor])
                            post.reply("User /u/" + pauthor + rmv_replystr)
                        else:
                            print('Replying to blank request ' + pid + ' by ' + pauthor)
                            post.reply(help_replystr)
                    else:
                        print('Will not reply to self')
        except AttributeError:
            pauthor = '[DELETED]'


def listen_for_requests():
    
    #Strings to search for
    search_string = ["@whiskybot"]
    
    
    reddit = redditCommon.reddit_login()
    wait_time = 1600 #only check every 1/2 hour, this sub doesn't go too crazy

    while True:
        sql = redditCommon.read_sql()
        cur = sql.cursor()
        
        try:
            #Check subreddits
            for subreddit in botInfo.subRedditList(): 
                scan_sub(reddit, subreddit, cur)
        except Exception as e:
            traceback.print_exc()
        
        sql.commit()
        cur.close()
        
        print('Running again in ' + str(wait_time) + ' seconds \n')
        time.sleep(wait_time)
        


def main(argv):
    listen_for_requests()
    
if __name__ == '__main__':
    main(sys.argv[1:])

