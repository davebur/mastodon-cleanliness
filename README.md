# mastodon-cleanliness
Mastodon - Keeping your followers and lists clean

# Purpose
For twitter, I keep everyone I follow in a list. It means that I can have lists for folks who I want to read everything that they post and other lists that are topic specific, or that I don't mind not seeing every post.

Mastodon allows lists but with one difference from Twitter, you must follow an account before you can put it into a list. So, I do that, but I also want to make sure that I haven't forgotten to put everyone into a list, as my main feed fills up. I also want to see who's following me and I'm not following back.

# Python Modules
You need to install Mastodon.py by running:
        `pip3 install Mastodon.py`

# Setup
You need an auth token.
1. Go to Settings -> Development -> New Application
2. Give the application the following permissions:
 - read
 - read:follows
 - read:lists
3. Put the access token into a file called access_token.txt

Finally, edit the script and set the base_url variable to your chosen mastodon server.

Now you can run the script.
