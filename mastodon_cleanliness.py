#!/usr/bin/env python3

"""
Script to read your mastodon followers and make sure that they
all present in at least one list
"""

import argparse
import logging
import os.path
import sys
from urllib.parse import urlparse
from mastodon import Mastodon, MastodonError, MastodonUnauthorizedError

# Change this to the server that you are using
BASE_URL = "https://YOUR_SERVER"
TOKEN_FILE = "PATH_TO_ACCESS_TOKEN"
# https://mastodonpy.readthedocs.io/en/stable/01_general.html#pagination
# says that 40 is the max returned, so let's stick with that
MAX_RESULT_RETURNED = 40
# Change to logging.INFO to get more messages displayed back
LOGGING_LEVEL = logging.CRITICAL


def get_full_handle(account, base_url):
    """
    Returns the full handle (username@domain) for an account.
    """
    if "@" in account.acct:
        return account.acct
    domain = urlparse(base_url).netloc
    return f"{account.acct}@{domain}"


def get_followers(mastodon, user_id, base_url):
    """
    Retrieves a dictionary of followers.
    """
    followers_list_accounts = {}
    my_followers = {}
    logging.info("My followers are ...")
    more_accounts = True

    while more_accounts:
        if not followers_list_accounts:
            logging.info(
                "Nothing in followers_list_accounts, getting first time.."
            )
            try:
                followers_list_accounts = mastodon.account_followers(
                    user_id, limit=MAX_RESULT_RETURNED
                )
            except MastodonError as error:
                print(
                    "Something when wrong when getting your list of "
                    "followers."
                )
                print("Bravely going to try to continue....")
                logging.critical("Error returned was %s", error)
                return {}

        else:
            logging.info(
                "Something in followers_list_accounts, pagination, "
                "getting next..."
            )
            try:
                followers_list_accounts = mastodon.fetch_next(
                    followers_list_accounts
                )
            except MastodonError as error:
                print(
                    "Something when wrong when getting your list of "
                    "followers."
                )
                print("Bravely going to try to continue....")
                logging.critical("Error returned was %s", error)
                # If pagination fails, we might just want to stop here
                break

        if not followers_list_accounts:
            break

        # If one of your followers has moved to another server, the
        # account.moved will be populated, so we need to remove this account.
        # For everyone else, we'll add them to my_followers{} and track
        # username
        for account in followers_list_accounts:
            if "moved" not in account:
                full_handle = get_full_handle(account, base_url)
                my_followers[account.id] = (
                    f"{full_handle}, {base_url}/@{account.acct}"
                )
            else:
                logging.info(
                    "Removing %s as a moved account", account.username
                )

        if len(followers_list_accounts) < MAX_RESULT_RETURNED:
            more_accounts = False

    return my_followers


def get_following(mastodon, user_id, my_followers, base_url):
    """
    Retrieves a dictionary of people the user is following.
    Removes them from my_followers if they follow back.
    """
    following_ids = {}
    follows = {}
    more_accounts = True

    while more_accounts:
        if not follows:
            logging.info("Nothing in follows, getting first time..")
            try:
                follows = mastodon.account_following(
                    user_id, limit=MAX_RESULT_RETURNED
                )
            except MastodonError as error:
                print(
                    "Something went wrong getting the list of folks you "
                    "are following."
                )
                print("Attempting to continue...")
                logging.critical("Error returned was....%s", error)
                return {}

        else:
            logging.info("Something in follows, pagination, getting next...")
            try:
                follows = mastodon.fetch_next(follows)
            except MastodonError as error:
                print(
                    "Something went wrong getting the list of folks you "
                    "are following."
                )
                print("Attempting to continue...")
                logging.critical("Error returned was....%s", error)
                break

        if not follows:
            break

        for user in follows:
            full_handle = get_full_handle(user, base_url)
            logging.info("\t%s", full_handle)
            logging.debug(user)
            following_ids[user.id] = full_handle

            if user.id in my_followers:
                logging.info(
                    "Removing follower %s, %s", user.acct, user.username
                )
                del my_followers[user.id]

        if len(follows) < MAX_RESULT_RETURNED:
            logging.info("follows was %s and now need to stop..", len(follows))
            more_accounts = False

    return following_ids


def process_lists(mastodon, following_ids):
    """
    Iterates through user lists and removes users from following_ids
    if they are found in a list.
    """
    try:
        my_lists = mastodon.lists()
    except MastodonError as error:
        print(
            "Something went wrong getting all of your lists. "
            "Attempting to continue..."
        )
        logging.critical("Error returned was....%s", error)
        return

    for mlist in my_lists:
        logging.info("%s -> %s", mlist.id, mlist.title)
        more_accounts = True
        list_accounts = {}

        while more_accounts:
            if not list_accounts:
                try:
                    list_accounts = mastodon.list_accounts(
                        mlist.id, limit=MAX_RESULT_RETURNED
                    )
                except MastodonError as error:
                    print("Something went wrong getting a list of your lists.")
                    print("Attempting to continue...")
                    logging.critical("Error returned was...%s", error)
                    # Ensure loop exit or handle gracefully
                    list_accounts = None
            else:
                try:
                    list_accounts = mastodon.fetch_next(list_accounts)
                except MastodonError as error:
                    print("Something went wrong getting a list of your lists.")
                    print("Attempting to continue...")
                    logging.critical("Error returned was...%s", error)
                    list_accounts = None

            if not list_accounts:
                break

            for account in list_accounts:
                logging.info(
                    "\t%s:%s %s", account.id, account.username, account.acct
                )
                if account.id in following_ids:
                    del following_ids[account.id]

            if len(list_accounts) < MAX_RESULT_RETURNED:
                more_accounts = False


def main():
    """
    Main function to sync mastodon lists.
    """
    parser = argparse.ArgumentParser(
        description="Script to read your mastodon followers and make sure "
                    "that they all present in at least one list"
    )
    parser.add_argument(
        "-d", "--debug",
        help="Print debug information",
        action="store_true"
    )
    parser.add_argument(
        "-u", "--url",
        help="The Mastodon server URL",
        default=BASE_URL
    )
    parser.add_argument(
        "-t", "--token",
        help="The path to the access token file",
        default=TOKEN_FILE
    )
    args = parser.parse_args()

    logging_level = LOGGING_LEVEL
    if args.debug:
        logging_level = logging.DEBUG
        print("Debug logging enabled")

    # Logging configuration.
    logging.basicConfig(
        level=logging_level, format="%(levelname)s-%(message)s"
    )

    # Let's make sure that the access_token file exists before reading it in.
    if not os.path.exists(args.token):
        print("No token file detected. Bailing out")
        logging.info("Unable to find %s where I expect it to be", args.token)
        sys.exit(1)
    else:
        mastodon = Mastodon(access_token=args.token, api_base_url=args.url)

    # Step one is to verify credentials, which makes sure we have a working
    # login but also gives us the id of the user, which we need later on.
    try:
        user_dict = mastodon.account_verify_credentials()
    except MastodonUnauthorizedError as error:
        print("Error occured when trying to validate your credentials.")
        logging.critical(
            "Here is the raw error message...%s", error
        )
        sys.exit(1)

    my_followers = get_followers(mastodon, user_dict.id, args.url)
    following_ids = get_following(
        mastodon, user_dict.id, my_followers, args.url
    )
    process_lists(mastodon, following_ids)

    print("Folks I\'m following but are not in lists...")
    for _, user in following_ids.items():
        print(f"\t{user}")

    print("\nWho I\'m not following back ...")
    for _, user in my_followers.items():
        print(f"\t{user}")


if __name__ == "__main__":
    main()
