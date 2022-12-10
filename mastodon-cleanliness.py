#!/usr/bin/env python3

# Script to read your mastodon followers and make sure that they
# all present in at least one list

from mastodon import Mastodon
import logging

base_url = 'https://CHANGE_TO_YOUR_MASTODON_INSTANCE'
token_file = 'access_token.txt'
max_result_returned = 40
logging_level = logging.CRITICAL

# Logging
logging.basicConfig(level=logging_level, format='%(levelname)s-%(message)s')

mastodon = Mastodon(
    access_token=token_file,
    api_base_url=base_url
)

user_dict = mastodon.account_verify_credentials()

# Get list of accounts that are following me
followers_list_accounts = {}
my_followers = {}

logging.info("My followers are ...")
more_accounts = True
while more_accounts:
    if len(followers_list_accounts) == 0:
        logging.info ("Nothing in followers_list_accounts, getting first time..")
        followers_list_accounts = mastodon.account_followers(user_dict.id, limit=max_result_returned)
    else:
        logging.info ("Something in followers_list_accounts, pagination, getting next...")
        followers_list_accounts = mastodon.fetch_next(followers_list_accounts)

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
        follows = mastodon.account_following(user_dict.id, limit=max_result_returned)
    else:
        logging.info ("Something in follows, pagination, getting next...")
        follows = mastodon.fetch_next(follows)
        
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
my_lists = mastodon.lists()

for list in my_lists:
    logging.info (f"{list.id} -> {list.title}")
    more_accounts = True
    list_accounts = {}

    while more_accounts:
        if len(list_accounts) == 0:
            list_accounts = mastodon.list_accounts(list.id, limit=max_result_returned)
        else:
            list_accounts = mastodon.fetch_next(list_accounts)

        for account in list_accounts:
            logging.info (f"\t{account.id}:{account.username} {account.acct}")
            del following_ids[account.id]

        if len(list_accounts) < max_result_returned:
            more_accounts = False

print ("Folks I'm following but are not in lists...")
for user in following_ids:
    print (f"\t{following_ids[user]}")

print ("")

print ("Who I'm not following back ...")
for user in my_followers:
    print (f"\t{my_followers[user]}")
