"""
collect.py

Collect data used in this project.
"""


from collections import Counter
import sys
import time
import configparser
from TwitterAPI import TwitterAPI
import pickle

consumer_key = 'L46cqMtL4N3tjZqJxB0aOYiXK'
consumer_secret = 'KTLEKN6ALtrDutfXWIOaZsXaIBmXeadtjZvUpQBMKBMVzIS1w1'
access_token = '904762936467619841-pJ4n1gMMitSPJ0ZHnzYJur5jYOQhqzL'
access_token_secret = 'UuculEqGVZt7ftJtmE8fIk1UJJFIFVcseOAJmkhv5nBrA'

def get_twitter():
    """
    get the twitter api using the tokens above
    """
    
    return TwitterAPI(consumer_key, consumer_secret, access_token, access_token_secret)


def read_screen_names(filename):
    """
    Read names from file. The names are the users we need to analyze.
    
    Params:
        filename....Name of the file to read.
    Returns:
        A list of strings, one per screen_name, in the order they are listed
        in the file.
    
    >>> read_screen_names('users.txt')
    ['taylorswift13', 'jk_rowling', 'EmmaWatson', 'juliannehough', 'lucyhale', 'cd_henderson', 'jessicaszohr', 'GraceEGold']
    """

    with open(filename, 'r') as f:
        content = f.read().splitlines()

    return content


def robust_request(twitter, resource, params, max_tries=5):
    """
    If a Twitter request fails, sleep for 15 minutes.
    Do this at most max_tries times before quitting.
    
    Args:
      twitter .... A TwitterAPI object.
      resource ... A resource string to request; e.g., "friends/ids"
      params ..... A parameter dict for the request, e.g., to specify
                   parameters like screen_name or count.
      max_tries .. The maximum number of tries to attempt.
    Returns:
      A TwitterResponse object, or None if failed.
    """
    
    for i in range(max_tries):
        request = twitter.request(resource, params)
        if request.status_code == 200:
            return request
        else:
            print('Got error %s \nsleeping for 15 minutes.' % request.text)
            sys.stderr.flush()
            time.sleep(61 * 15)


def get_data_user(twitter, screen_names):
    """
    Retrieve the Twitter user objects for each screen_name.
    
    Params:
        twitter........The TwitterAPI object.
        screen_names...A list of strings, one per screen_name
    Returns:
        A list of dicts, one per user, containing all the user information
        (screen_name, id, friends_id)

    >>> twitter = get_twitter()
    >>> users = get_users(twitter, ['twitterapi', 'twitter'])
    >>> [u['id'] for u in users]
    [6253282, 783214]
    """

    data_user = []
    for name in screen_names:
        request = robust_request(twitter, 'users/lookup', {'screen_name': name}, max_tries=5)
        user = [val for val in request]
        friends = []
        request = robust_request(twitter, 'friends/ids', {'screen_name': name, 'count': 5000}, max_tries=5)
        friends = sorted([str(val) for val in request])
        fr = {'screen_name': user[0]['screen_name'],
             'id': str(user[0]['id']),
             'friends_id': friends}
        data_user.append(fr)
   
    return data_user


def get_tweets(twitter, screen_name, num_tweets):
    """
    Retrieve tweets of the user.

    params:
        twiiter......The TwitterAPI object.
        screen_name..The user to collect tweets from.
        num_tweets...The number of tweets to collect.
    returns:
        A list of strings, one per tweet.
    """

    request = robust_request(twitter, 'search/tweets', {'q': screen_name, 'count': num_tweets})
    tweets = [a['text'] for a in request]

    return tweets


def save_obj(obj, name):
    """
    store, list of dicts
    """
    
    with open(name + '.pkl', 'wb') as objec:
        pickle.dump(obj, objec)


def main():
    print("Data Imported")
    twitter = get_twitter()
    print("Twitter Information fetched")
    screen_names = read_screen_names('users.txt')
    print('Established Twitter connection.')
    print('Read screen names:\n%s' % screen_names)
    data_user = get_data_user(twitter, screen_names)
    save_obj(data_user, 'twit_user')
    print("users info saved.")
    tweets = get_tweets(twitter, screen_names[0], 100)
    save_obj(tweets, 'tweets')
    print("%d tweets saved." % (len(tweets)))


if __name__ == '__main__':
    main()





