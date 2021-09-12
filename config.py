import os

WEBHOOK_PASSPHRASE = os.environ.get("WEBHOOK_PASSPHRASE")

API_KEY = os.environ.get("API_KEY")
API_SECRET = os.environ.get("API_SECRET")

MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")

RISK = 0.05

TEST = 0  #Live Trading

#TEST = 1  #Test Orders Only

#TEST = 2 #ACCOUNT Balance will have a fixed Amount. 

TEST_ACCOUNT = 1000
