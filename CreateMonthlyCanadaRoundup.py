
import sys
import time
import random
import sqlite3
import itertools
from datetime import datetime
from datetime import timedelta

from calendar import monthrange

import botInfo
import redditCommon


DEBUG = True


####################
##Function for adding text to the post
####################            
def addToPost(post_list, title, subreddit):
    
    if len(post_list) == 0:
        return ""
    
    #Randomize the array a bit.  don't reward people for signing up first
    random.shuffle(post_list)

    toReturnText=""
    if len(title) > 0:
        toReturnText="""

**[%s](http://reddit.com/r/%s)**

""" % (title, subreddit)

    for whiskypost in post_list:

        #Get the url we want to use
        linkText = "([comments](%s))" %(whiskypost.shortlink)
        if not whiskypost.is_self: #If it's NOT a self post
            linkText = "([link](%s)/[comments](%s))" %(whiskypost.url, whiskypost.shortlink)


        toReturnText += """* /u/%s - %s %s
""" % (whiskypost.author.name, whiskypost.title, linkText)


    #once we've looped through, add a line break
    toReturnText += """

&nbsp;  

"""  
    return toReturnText


def get_post_list(user_posts, subreddit):
    if subreddit == "scotchswap":
        ft = []
        iso = []
        general = []
        
        for user, posts in user_posts.items():
            for post in posts[subreddit]:
                if "ft:" in post.title.lower():
                    ft.append(post)
                elif "iso:" in post.title.lower():
                    iso.append(post)
                else:
                    general.append(post)
    
        return (ft, iso, general)
        
    else:
        post_list = []

        for user, posts in user_posts.items():
            post_list.extend(posts[subreddit])
            
        return post_list
        

def create_post_text(user_posts):
    DATE=datetime.today()
    
    ##Initialize the post title and text
    PostTitle = "Canada Whisky's Monthly Roundup: " + str(DATE.month) + "/" + str(DATE.day) + "/" + str(DATE.year)
    PostText = """
Welcome to /r/canadawhisky's Monthly Review Roundup, posted on %s/%s/%s

&nbsp;  

""" % (str(DATE.month), str(DATE.day), str(DATE.year))
    
        
    ########################
    ##Create the content for our post
    
    reviews_found = False
        
    for sub in ["Scotch", "Bourbon", "WorldWhisky"]:
        posts = get_post_list(user_posts, sub.lower())
        
        if (len(posts)) > 0:
            
            if not reviews_found:
                reviews_found = True
                PostText += """**Reviews Posted by /r/CanadaWhisky Users**
  
===
---
  
"""
                
            
            PostText += addToPost(posts, sub + " Reviews", sub)
            
    whiskyporn_posts = get_post_list(user_posts, "whiskyporn")
    if len(whiskyporn_posts) > 0:
        PostText += """**/r/CanadaWhisky's Whisky Porn**
  
===
---
  
"""
        PostText += addToPost(whiskyporn_posts, '', '')
        
    discussion_posts = get_post_list(user_posts, "discussion")
    if len(discussion_posts) > 0:
        PostText += """**Other Whiskynetwork Posts**

===
---

"""   
        PostText += addToPost(discussion_posts, '', '')        

        
    ft_posts, iso_posts, sw_posts = get_post_list(user_posts, "scotchswap")
    
    if len(ft_posts + iso_posts + sw_posts) > 0:
        PostText += """**ScotchSwap Posts by /r/CanadaWhisky Subscribers**

===
---

"""	    
    if len(sw_posts) > 0:
        PostText += addToPost(sw_posts, 'ScotchSwap Posts', 'ScotchSwap')
    if len(ft_posts) > 0 or len(iso_posts) > 0:
        PostText += addToPost(iso_posts + ft_posts, 'ScotchSwap FT/ISO Posts', 'ScotchSwap')
        
        
    PostText +="""

To be added to future roundups, comment on this thread "@whiskybot add". To be removed, comment "@whiskybot remove"
"""
        
    #add the file signature
    PostText += botInfo.postSignature()
    
    return (PostTitle, PostText)


def main(argv):
    
    global DEBUG
    
    roundup_subreddit = "canadawhisky"

    #####################
    ## Get reddit connection object and DB
    #####################
    reddit = redditCommon.reddit_login()

    sql = redditCommon.read_sql()
    cur = sql.cursor()
    
    ########################
    ## Get relevant user posts
    ########################
    user_posts = {}
    last_month = datetime.today() - timedelta(days=28)
    mdays = monthrange(last_month.year, last_month.month)[1]
    min_post_date = datetime.today() - timedelta(days=mdays, hours=1)
    
    print (min_post_date)
    
    users = cur.execute('SELECT USER FROM users WHERE SUBREDDIT=?', [roundup_subreddit])
    for user in users:
        user = user[0]
        user_posts[user] = redditCommon.getUserPosts(reddit, user, min_post_date)
    
    ##################
    ## Create post from user posts
    ##  The return from create_post_text is a tuple with title and text
    ##################
    post_data = create_post_text (user_posts)
    
    ##################
    ## Submit to Reddit
    ##################
    if DEBUG:
        print(post_data[0], post_data[1])
    else:
        print ("Submitting to Reddit")
        submit_result = reddit.subreddit(roundup_subreddit).submit(post_data[0], selftext=post_data[1])
        #PostURL = submit_result.url

    sql.commit()
    cur.close()
    print ("Closing")
    
    return
    

if __name__ == '__main__':
    main(sys.argv[1:])


