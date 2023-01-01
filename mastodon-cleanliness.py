#!/usr/bin/env python3

# Script to read your mastodon followers and make sure that they
# all present in at least one list

from mastodon import Mastodon
import logging
import os.path

# Change this to the server that you are using
base_url = 'https://CHANGE_TO_YOUR_MASTODON_INSTANCE'
token_file = 'access_token.txt'
# https://mastodonpy.readthedocs.io/en/stable/01_general.html#pagination says that
# 40 is the max returned, so let's stick with that
max_result_returned = 40
# Change to logging.INFO to get more messages displayed back
logging_level = logging.CRITICAL

# Logging configuration.
logging.basicConfig(level=logging_level, format='%(levelname)s-%(message)s')

# Let's make sure that the access_token file exists before reading it in.
if os.path.exists(token_file) == False:
    print ("No token file detected. Bailing out")
    logging.info(f"Unable to find {token_file} where I expect it to be")

    exit(1)
else:
    mastodon = Mastodon(
        access_token=token_file,
        api_base_url=base_url
    )

# Step one is to verify credentials, which makes sure we have a working login
# but also gives us the id of the user, which we need later on.
try:
    user_dict = mastodon.account_verify_credentials()
except Exception as error:
    print ("Error occured when trying to validate your credentials.")
    logging.crit(f"Here is the raw error message...{error}")
    exit(1)

# Now we need a list of accounts that are following the user
# We will keep pulling the list of accounts until the final go when the number
# returned is less than the max per pagination, which is the clue that we're at 
# the end
followers_list_accounts = {}
my_followers = {}
logging.info("My followers are ...")
more_accounts = True

while more_accounts:
    if len(followers_list_accounts) == 0:
        logging.info ("Nothing in followers_list_accounts, getting first time..")
        try:
            followers_list_accounts = mastodon.account_followers(user_dict.id, limit=max_result_returned)
        except Exception as error:
            print ("Something when wrong when getting your list of followers. Bravely going to try to continue....")
            logging.crit(f"Error returned was {error}")

    else:
        logging.info ("Something in followers_list_accounts, pagination, getting next...")
        try:
            followers_list_accounts = mastodon.fetch_next(followers_list_accounts)
        except Exception as error:
            print ("Something when wrong when getting your list of followers. Bravely going to try to continue....")
            logging.crit(f"Error returned was {error}")

    # If one of your followers has moved to another server, the account.moved will be
    # populated, so we need to remove this account.
    # For everyone else, we'll add them to my_followers{} and track username
    for account in followers_list_accounts:
        if 'moved' not in account.keys():
            my_followers[account.id] = f"{account.username}, {base_url}/@{account.acct}"
        else:
            logging.info(f"Removing {account.username} as a moved account")

    if len(followers_list_accounts) < max_result_returned:
        more_accounts = False

#Get who I'm following
following_ids = {}
follows = {}
more_accounts = True

while more_accounts:
    if len(follows) == 0: 
        logging.info ("Nothing in follows, getting first time..")
        try:
            follows = mastodon.account_following(user_dict.id, limit=max_result_returned)
        except Exception as error:
            print ("Something went wrong getting the list of folks you are following. Attempting to continue...")
            logging.crit(f"Error returned was....{error}")

    else:
        logging.info ("Something in follows, pagination, getting next...")
        try:
            follows = mastodon.fetch_next(follows)
        except Exception as error:
            print ("Something went wrong getting the list of folks you are following. Attempting to continue...")
            logging.crit(f"Error returned was....{error}")

    for user in follows:
        logging.info (f"\t{user.username}")
        logging.debug (user)
        following_ids[user.id] = user.username
    
        if user.id in my_followers:
            logging.info (f"Removing follower {user.acct}, {user.username}")
            del my_followers[user.id]

    if len(follows) < max_result_returned:
        logging.info (f"follows was {len(follows)} and now need to stop..")
        more_accounts = False

# My lists
try:
    my_lists = mastodon.lists()
except Exception as error:
    print ("Something went wrong getting all of your lists. Attempting to continue...")
    logging.crit(f"Error returned was....{error}")

for list in my_lists:
    logging.info (f"{list.id} -> {list.title}")
    more_accounts = True
    list_accounts = {}

    while more_accounts:
        if len(list_accounts) == 0:
            try:
                list_accounts = mastodon.list_accounts(list.id, limit=max_result_returned)
            except Exception as error:
                print ("Something went wrong getting a list of your lists. Attempting to continue...")
                logging.crit(f"Error returned was...{error}")
        else:
            try:
                list_accounts = mastodon.fetch_next(list_accounts)
            except Exception as error:
                print ("Something went wrong getting a list of your lists. Attempting to continue...")
                logging.crit(f"Error returned was...{error}")
 

        for account in list_accounts:
            logging.info (f"\t{account.id}:{account.username} {account.acct}")
            del following_ids[account.id]

        if len(list_accounts) < max_result_returned:
            more_accounts = False

print ("Folks I'm following but are not in lists...")
for user in following_ids:
    print (f"\t{following_ids[user]}")


print ("\nWho I'm not following back ...")
for user in my_followers:
    print (f"\t{my_followers[user]}")
