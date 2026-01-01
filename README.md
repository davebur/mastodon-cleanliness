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
1. Go to the website of the Mastodon server instance that you are using.
2. Go to Settings -> Development -> New Application
3. Give the application the following permissions:
 - read
 - read:follows
 - read:lists
4. Put the access token into a file called access_token.txt

# Usage

You can run the script directly. By default, it looks for `access_token.txt` in the current directory and uses a placeholder base URL (which you can change in the script).

However, you can specify these via command line arguments:

```bash
python3 mastodon_cleanliness.py [-h] [-d] [-u URL] [-t TOKEN]
```

## Arguments

- `-h`, `--help`: Show the help message and exit.
- `-d`, `--debug`: Enable debug logging to see more detailed output.
- `-u URL`, `--url URL`: The Mastodon server URL (e.g., `https://mastodon.social`).
- `-t TOKEN`, `--token TOKEN`: Path to the access token file.

## Example

```bash
python3 mastodon_cleanliness.py -u https://mastodon.ie -t ~/.mastodon.ie_access_token.txt -d
```