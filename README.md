Whisky Bot
================

Whisky Bot is a python based Reddit Bot that uses Reddits Python Reddit API Wrapper (PRAW)

It is unobtrustive in its commenting as it only comments when called. 

It serves two functions; 

* Scanning comments for @whiskybot calls to add or remove users from the roundup database
* Creating weekly posts for user reviews and whiskyporn submissions, and a separate post for scotchswap posts

Commands
================

Valid calls are:

* @whiskybot add
* @whiskybot remove

The first adds your username to the weekly roundup, the second removes you.  If the bot is called using @whiskybot but one of these calls is not provided the bot responds with a list of valid calls. 

Files
================

This bot has two main python files.  

The first scans all comments added to /r/dcwhisky for references to itself, and adds or removes users from its database per their request. 

The second performs weekly posts of two types; review and whiskyporn roundup, and /r/scotchswap posts, but successful swaps and ISO/FT threads. 

As a note, to run any of these locally you must set up the botInfo.py to return your botname, its password, the userAgent, the subreddit it works on, and a signature to add to your posts. 
