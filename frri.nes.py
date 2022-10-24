#!/usr/bin/python3
# system
import time
import os

# proprietary
import tweepy

# user
from secrets import Secrets

#---
#tweepy interfacing
client = tweepy.Client(consumer_key = Secrets.API_KEY,
						consumer_secret = Secrets.API_SECRET,
						access_token = Secrets.OAUTH_TOKEN,
						access_token_secret = Secrets.OAUTH_TOKEN_SECRET)

#---
# Script
CTRL_FILE = "/proc/nes_ctrl"
CTRL_FILE_BYTES = 4
CTRL_POLLING_RATE = 60.

nes = os.open(CTRL_FILE, os.O_RDONLY)
while(True):
    value = (os.read(nes, CTRL_FILE_BYTES)).decode().strip()
    time.sleep(1. / CTRL_POLLING_RATE)
    print(value)

os.close(nes)

#message = "[Furmeet Roaming Relay Interface is now Online]" 
#response = client.create_tweet(text=message)
