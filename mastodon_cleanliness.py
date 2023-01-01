#!/usr/bin/env python3

"""
Script to read your mastodon followers and make sure that they
all present in at least one list
"""

import logging
import os.path
import sys
from mastodon import Mastodon

# Change this to the server that you are using
BASE_URL = 'https://ioc.exchange'
TOKEN_FILE = 'access_token.txt'
# https://mastodonpy.readthedocs.io/en/stable/01_general.html#pagination says that
# 40 is the max returned, so let's stick with that
MAX_RESULT_RETURNED = 40
# Change to logging.INFO to get more messages displayed back
LOGGING_LEVEL = logging.CRITICAL

# Logging configuration.
logging.basicConfig(level=LOGGING_LEVEL, format='%(levelname)s-%(message)s')

# Let's make sure that the access_token file exists before reading it in.
if os.path.exists(TOKEN_FILE) is False:
    print ("No token file detected. Bailing out")
    logging.info("Unable to find %s where I expect it to be", TOKEN_FILE)

    sys.exit(1)
else:
    mastodon = Mastodon(
        access_token=TOKEN_FILE,
        api_base_url=BASE_URL
    )

# Step one is to verify credentials, which makes sure we have a working login
# but also gives us the id of the user, which we need later on.
try:
    user_dict = mastodon.account_verify_credentials()
except Exception as error:
    print ("Error occured when trying to validate your credentials.")
    logging.critical("Here is the raw error message...%s", error)
    sys.exit(1)

# Now we need a list of accounts that are following the user
# We will keep pulling the list of accounts until the final go when the number
# returned is less than the max per pagination, which is the clue that we're at
# the end
followers_list_accounts = {}
my_followers = {}
logging.info("My followers are ...")
MORE_ACCOUNTS = True

while MORE_ACCOUNTS:
    if len(followers_list_accounts) == 0:
        logging.info ("Nothing in followers_list_accounts, getting first time..")
        try:
            followers_list_accounts = mastodon.account_followers(user_dict.id,
                limit=MAX_RESULT_RETURNED)
        except Exception as error:
            print ("Something when wrong when getting your list of followers.")
            print ("Bravely going to try to continue....")
            logging.critical("Error returned was %s", error)

    else:
        logging.info ("Something in followers_list_accounts, pagination, getting next...")
        try:
            followers_list_accounts = mastodon.fetch_next(followers_list_accounts)
        except Exception as error:
            print ("Something when wrong when getting your list of followers.")
            print ("Bravely going to try to continue....")
            logging.critical("Error returned was %s", error)

    # If one of your followers has moved to another server, the account.moved will be
    # populated, so we need to remove this account.
    # For everyone else, we'll add them to my_followers{} and track username
    for account in followers_list_accounts:
        if 'moved' not in account.keys():
            my_followers[account.id] = f"{account.username}, {BASE_URL}/@{account.acct}"
        else:
            logging.info("Removing %s as a moved account", account.username)

    if len(followers_list_accounts) < MAX_RESULT_RETURNED:
        MORE_ACCOUNTS = False

#Get who I'm following
following_ids = {}
follows = {}
MORE_ACCOUNTS = True

while MORE_ACCOUNTS:
    if len(follows) == 0:
        logging.info ("Nothing in follows, getting first time..")
        try:
            follows = mastodon.account_following(user_dict.id, limit=MAX_RESULT_RETURNED)
        except Exception as error:
            print ("Something went wrong getting the list of folks you are following.")
            print ("Attempting to continue...")
            logging.critical("Error returned was....%s", error)

    else:
        logging.info ("Something in follows, pagination, getting next...")
        try:
            follows = mastodon.fetch_next(follows)
        except Exception as error:
            print ("Something went wrong getting the list of folks you are following.")
            print ("Attempting to continue...")
            logging.critical("Error returned was....%s", error)

    for user in follows:
        logging.info ("\t%s", user.username)
        logging.debug (user)
        following_ids[user.id] = user.username

        if user.id in my_followers:
            logging.info ("Removing follower %s, %s", user.acct, user.username)
            del my_followers[user.id]

    if len(follows) < MAX_RESULT_RETURNED:
        logging.info ("follows was %s and now need to stop..", len(follows))
        MORE_ACCOUNTS = False

# My lists
try:
    my_lists = mastodon.lists()
except Exception as error:
    print ("Something went wrong getting all of your lists. Attempting to continue...")
    logging.critical("Error returned was....%s", error)

for mlist in my_lists:
    logging.info ("%s -> %s", mlist.id, mlist.title)
    MORE_ACCOUNTS = True
    list_accounts = {}

    while MORE_ACCOUNTS:
        if len(list_accounts) == 0:
            try:
                list_accounts = mastodon.list_accounts(mlist.id, limit=MAX_RESULT_RETURNED)
            except Exception as error:
                print ("Something went wrong getting a list of your lists.")
                print ("Attempting to continue...")
                logging.critical("Error returned was...%s", error)
        else:
            try:
                list_accounts = mastodon.fetch_next(list_accounts)
            except Exception as error:
                print ("Something went wrong getting a list of your lists.")
                print ("Attempting to continue...")
                logging.critical("Error returned was...%s", error)

        for account in list_accounts:
            logging.info ("\t%s:%s %s", account.id, account.username, account.acct)
            del following_ids[account.id]

        if len(list_accounts) < MAX_RESULT_RETURNED:
            MORE_ACCOUNTS = False

print ("Folks I'm following but are not in lists...")
for user in following_ids:
    print (f"\t{following_ids[user]}")

print ("\nWho I'm not following back ...")
for user in my_followers:
    print (f"\t{my_followers[user]}")
