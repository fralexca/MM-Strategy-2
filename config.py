import os

WEBHOOK_PASSPHRASE = os.environ.get("WEBHOOK_PASSPHRASE")

API_KEY = os.environ.get("API_KEY")
API_SECRET = os.environ.get("API_SECRET")

MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")

RISK = os.environ.get("RISK")

TEST = os.environ.get("TEST") #Trading Settings (0=Live Trading), (1=Test Trading), (2=Fixed Account Balance)

#TEST = 0  #Live Trading

#TEST = 1  #Test Orders Only

#TEST = 2 #ACCOUNT Balance will have a fixed Amount. 

TEST_ACCOUNT = os.environ.get("TEST_ACCOUNT")
