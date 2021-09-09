import json, config, requests, os
from re import sub
from flask import Flask, request, render_template, redirect, url_for, jsonify
from flask_mail import Mail, Message
from binance.client import Client
from binance.enums import *
#from pymongo import MongoClient


app = Flask(__name__)

client = Client(config.API_KEY, config.API_SECRET)

# client_db = MongoClient("mongodb+srv://jimerictibayan2012:Juliusaiden1@mmprotrader1.tqdyf.mongodb.net/test")
# app.db = client_db.TradingBot





app.config['MAIL_SERVER']='smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = config.MAIL_USERNAME    
app.config['MAIL_PASSWORD'] = config.MAIL_PASSWORD    
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

mail = Mail(app)

#Get the Config from the Database

def order(side, quantity, symbol, order_type=ORDER_TYPE_MARKET):  #side = Buy or Sell 
    try:
        print("sending order")
        order = client.create_order(symbol=symbol, side=side, type=order_type, quantity=quantity)
        print(order)
    except Exception as e:
        print("an exception occured - {}".format(e))
        return False

    return True

def test_order(side, price, symbol, order_type, body, mode):
    if mode == "EXIT":
        try:
            print('Sending Test Order')
            order = client.create_test_order(
            symbol=symbol,
            side=side,
            type=order_type,
            #timeInForce=TIME_IN_FORCE_GTC,
            quantity=price)
            #quoteOrderQty = price)
        except Exception as e:
            print("an exception occured - {}".format(e))
            return False

        return True
    
    else:
        try:
            print('Sending Test Order')
            order = client.create_test_order(
            symbol=symbol,
            side=side,
            type=order_type,
            #timeInForce=TIME_IN_FORCE_GTC,
            #quantity=quantity
            quoteOrderQty = price)
        except Exception as e:
            print("an exception occured - {}".format(e))
            return False

        return True

#Begin of Jim
def create_margin_order(side, price, symbol, order_type, body, mode, side_effect, subject):
    if mode == "EXIT":

        try:
            print('Sending Margin Order')
            order = client.create_margin_order(
            symbol=symbol,
            side=side,
            type=order_type,
            #timeInForce=TIME_IN_FORCE_GTC,
            quantity=price,
            sideEffectType = side_effect)
            #quoteOrderQty = price)
        except Exception as e:
            print("an exception occured - {}".format(e))
            body = body + "an exception occured - " + format(e)
            return False, body

        return order, body

    else:
        try:
            print('Sending Margin Order')
            order = client.create_margin_order(
            symbol=symbol,
            side=side,
            type=order_type,
            quoteOrderQty = price,
            sideEffectType = side_effect)
        except Exception as e:
            print("an exception occured - {}".format(e))
            body = body + "an exception occured - " + format(e)
            return False, body

        return order, body


def get_account():

    print("Getting Account Balances.....")
    account = client.get_margin_account()
    return account


def get_price(in_symbol):
    symbol = client.get_symbol_ticker(symbol = in_symbol)
    return symbol


def check_decimals(symbol):
    info = client.get_symbol_info(symbol)
    val = info['filters'][2]['stepSize']
    decimal = 0
    is_dec = False
    for c in val:
        if is_dec is True:
            decimal += 1
        if c == '1':
            break
        if c == '.':
            is_dec = True
    return decimal, info

def check_price_decimals(symbol):
    info = client.get_symbol_info(symbol)
    val = info['filters'][0]['tickSize']
    decimal = 0
    is_dec = False
    for c in val:
        if is_dec is True:
            decimal += 1
        if c == '1':
            break
        if c == '.':
            is_dec = True
    return decimal, info

def create_stop_lost(side, quantity, symbol, order_type, price, stopPrice, body):

    try:
        stop_lost_order = client.create_margin_order(
        symbol=symbol,
        side=side,
        type=order_type,
        timeInForce=TIME_IN_FORCE_GTC,
        quantity=quantity,
        price=price,
        stopPrice=stopPrice,
        sideEffectType="MARGIN_BUY")

    except Exception as e:
        print("Error in Stop Lost Creation - {}".format(e))
        body = body + "Error in Stop Lost Creation - {}".format(e) + "\n"
        return False, body

    return True, body

def get_account_balance():
    account_btc = get_account()
    print("BTC Account : " + account_btc["totalNetAssetOfBtc"])
    
    #Calculate the Account to USDT
    btc_price = get_price("BTCUSDT")
    account_usdt = float(account_btc["totalNetAssetOfBtc"]) * float(btc_price['price'])
    print("USDT Account : " + str(account_usdt))

    btc_account = float(account_btc["totalNetAssetOfBtc"])

    return btc_account, account_usdt

def get_test_account_btc(account_usdt):
    btc_price = get_price("BTCUSDT")
    account_btc = account_usdt / float(btc_price['price'])

    return account_btc

def calc_position(data, account_btc, account_usdt, SL, body):
    pair_end = data['ticker'][-3:]
    #SL = data['stoploss'] / 100

    position_btc = ( account_btc * config.RISK ) / SL
    print("Position in BTC: " + str(position_btc))
    body = body + "Position in BTC: " + str(position_btc) + "\n"

    position_usdt = (account_usdt * config.RISK) / SL
    print("Position in USDT: " + str(position_usdt))
    body = body + "Position in USDT: " + str(position_usdt) + "\n"

    body = body + "\n" #Add Line

    if pair_end == "BTC":
        position = position_btc    
    else: 
        position = position_usdt

    return position, body

def calc_coin_quantity(data, order_id):

    # coin_price = get_price(data['ticker'])
    # decimal, info = check_decimals(data['ticker'])
    # print("The Current Price of " + data['ticker'] + " is " + coin_price['price'])
    # quantity = position / float(coin_price['price'])   
    # order_quantity = "{:0.0{}f}".format(quantity, decimal)

    order = client.get_margin_order(symbol=data['ticker'],orderId=order_id)
    if order:

        print("The Order Quantity for " + data['ticker'] + " is " + order['origQty'] )

    return order['origQty']

def get_exit_quantity(data, body):
    try:
        orders = client.get_open_margin_orders(symbol=data['ticker'])
        order_quantity = 0
        order_id = 0
    except Exception as e:
        print("an exception occured - {}".format(e))
        body = body + "an exception occured - " + format(e)
        return False, 0, body
    
    #print (orders)

    if orders and orders[0]['type'] == "STOP_LOSS_LIMIT":

        
    
        quantity = float(orders[0]['origQty'])
        decimal, info = check_decimals(data['ticker'])
        order_quantity = "{:0.0{}f}".format(quantity, decimal)
        order_id = int(orders[0]['orderId'])

        return order_quantity, order_id, body

    else:
        # body = body + "No Existing Trade"
        return False, False, body


def execute_order(side, position, ticker, order_type, body, message, side_effect, subject):
    mode = ""

    if config.TEST == 1: #Test Mode, Test Order will be created
        create_order = test_order(side, position, ticker, order_type, body, mode)
        entry_price = get_price(ticker)
        print (entry_price) 
        body = body + "Test Order ENTRY PRICE is " + str(entry_price['price'])
        subject = "Test Order"
        
    
    elif config.TEST== 0 or config.TEST == 2: #True Order will be created
        #if order_quantity:
        create_order, body = create_margin_order(side, position, ticker, order_type, body, mode, side_effect, subject)
        if create_order:
            entry_price = float(create_order['fills'][0]['price'])
            order_id = create_order['orderId']
            print (entry_price)    
            return entry_price, order_id, body, subject

    return False, False, body, subject


def execute_order_exit(side, quantity, ticker, order_type, body, message, subject):
        
    mode = "EXIT"
    
    if config.TEST == 1: #Test Mode, Test Order will be created       
        create_order = test_order(side, quantity, ticker, order_type, body, mode)
        entry_price = get_price(ticker)
        print (entry_price) 
        body = body + "Test Order EXIT PRICE is " + str(entry_price['price'])
        subject = "Test Order"
    
    elif config.TEST== 0 or config.TEST == 2: #True Order will be created
        #if order_quantity:
        create_order, body = create_margin_order(side, quantity, ticker, order_type, body, mode, "MARGIN_BUY", subject)
        if create_order:
            entry_price = float(create_order['fills'][0]['price'])
            order_id = create_order['orderId']
            print (entry_price)    
            return entry_price, True, body, subject
        else:
            return False, False, body, subject

    return False, False, body, subject

def create_order(data, position, body, side_effect):

    entry_price = ""
    subject = "Failed"

    if data['message'] == "ENTRY LONG":
        print("This is ENTRY LONG")
        side = SIDE_BUY
        order_type = ORDER_TYPE_MARKET
        #Execute the Order
        entry_price, order_id, body, subject = execute_order(side, position, data['ticker'], order_type, body, data['message'], side_effect,subject)
        
    elif data['message'] == "ENTRY SHORT":
        print("This is ENTRY SHORT")
        side = SIDE_SELL
        order_type = ORDER_TYPE_MARKET
        #Execute the Order
        entry_price, order_id, body, subject = execute_order(side, position, data['ticker'], order_type, body, data['message'], "MARGIN_BUY", subject)
        
    elif data['message'] == "EXIT LONG":
        #print("This is EXIT LONG")
        side = SIDE_SELL
        order_type = ORDER_TYPE_MARKET

        #Get the Coin Quantity
        order_quantity, order_id, body = get_exit_quantity(data, body)

        if order_id: #If there is an existing Trade Cancel the SL and Exit the Trade
            if config.TEST != 1:
                try:
                    result = client.cancel_margin_order(symbol=data['ticker'],orderId=order_id)
                except Exception as e:
                    print("Error - {}".format(e))
                    body = body + "Error - " + format(e) + "\n"
                    subject = "Fail!"
                    return False, False, body, subject

                print("Stop Loss Order is cancelled Successfully!")
                body = body + "Stop Loss Order is cancelled Successfully!" + "\n"
            
            else:
                print("Test Only: The Stop Lost Order for " + data['ticker'] + "is now cancelled")

        else:
            body = body + "There is no Existing Trade" + "\n"
            subject = "No Trade Exists"
            print("There is no Exisiting Trade")
            return False, False, body, subject

        # print (order_quantity)
        # print (order_id)

        #Execute the Order
        entry_price, order_id, body, subject = execute_order_exit(side, order_quantity, data['ticker'], order_type, body, data['message'], subject)
        if entry_price:
            body = body + "EXIT LONG is successfully Executed!" + "\n"
            body = body + "Exit Price : " + str(entry_price) + "\n"
            subject = "Success!"
            print("EXIT LONG is successfully Executed!")
            print("Exit Price : " + str(entry_price))

    elif data['message'] == "EXIT SHORT":
        print("This is EXIT SHORT")
        side = SIDE_BUY
        order_type = ORDER_TYPE_MARKET

        #Get the Coin Quantity
        order_quantity, order_id, body = get_exit_quantity(data, body)

        if order_id: #If there is an existing Trade Cancel the SL and Exit the Trade
            if config.TEST != 1:
                try:
                    result = client.cancel_margin_order(symbol=data['ticker'],orderId=order_id)
                except Exception as e:
                    print("Error - {}".format(e))
                    body = body + "Error - " + format(e) + "\n"
                    subject = "Fail!"
                    return False, False, body, subject

                print("Stop Loss Order is cancelled Successfully!")
                body = body + "Stop Loss Order is cancelled Successfully!" + "\n"
            
            else:
                print("Test Only: The Stop Lost Order for " + data['ticker'] + "is now cancelled")

        else:
            body = body + "There is no Existing Trade" + "\n"
            subject = "No Trade Exists"
            print("There is no Exisiting Trade")
            return False, False, body, subject


        #Execute the Order
        entry_price, order_id, body, subject = execute_order_exit(side, order_quantity, data['ticker'], order_type, body, data['message'], subject)
        if entry_price:
            body = body + "EXIT SHORT is successfully Executed!" + "\n"
            body = body + "Exit Price : " + str(entry_price) + "\n"
            subject = "Success!"
            print("EXIT SHORT is successfully Executed!")
            print("Exit Price : " + str(entry_price))

    return entry_price, order_id, body, subject

def calculate_stop_loss(data):

    if data['message'] == "ENTRY LONG":
        SL = 1 - (data["stopprice"]/data["entryprice"]) 
    elif data['message'] == "ENTRY SHORT":
        SL = (data["stopprice"]/data["entryprice"]) - 1
    return SL


def create_email(data, body, subject):
    msg = Message(data['ticker'] + " - " + data['message'] + " - " + subject, sender =   'PRO-TRADER BOT@mailtrap.io', recipients = ['Dummy@dummy.com'])
    msg.body = body
    mail.send(msg)

    return "Message Sent"

def get_asset_balance(data):
    balance = 0
    asset = data['ticker'][-3:]

    if asset == "BTC":
        in_asset = asset
        n = 3
    else:
        in_asset = "USDT"
        n = 4 

    if data['message'] == "ENTRY SHORT":
        in_asset = data['ticker'][:len(data['ticker']) - n]

    print("Asset coin is " + in_asset)

    try:
        #balance = client.get_margin_asset(asset=in_asset)
        margin_account = client.get_margin_account()
    
    except Exception as e:
        print("an exception occured - {}".format(e))
        return False

    if margin_account:
        for x in margin_account['userAssets']:
            if x['asset'] == in_asset:
                balance = float(x['free'])

    return balance, in_asset

def borrow_asset(balance, position, asset, data, body):
    transaction = False

    if data['message'] == "ENTRY LONG":
        if balance < position:
            #Determine the Amount to be borrowed
            to_borrow = position - balance
            body = body + "Need to borrow : " + str(to_borrow) + " " + asset + "\n"
            print ("Need to borrow : " + str(to_borrow) + " " + asset)
            
            if config.TEST != 1:
                body = body + "Borrowing..." + "\n"
                print ("Borrowing...")
                transaction = execute_loan(asset, to_borrow)  #Borrow the Asset
            else:
                print('Test Only! Should borrow ' + str(to_borrow) + str(asset))
            
            if transaction:
                body = body + "Borrowed Amount :" + str(to_borrow) + asset + "\n"
                print ("Borrowed Amount :" + str(to_borrow) + asset)

        elif data['message'] == "ENTRY SHORT":
            print()

    return transaction, body

def execute_loan(asset, to_borrow):
    try:
        transaction = client.create_margin_loan(asset=asset, amount=to_borrow)
    
    except Exception as e:
        print("an exception occured - {}".format(e))
        return False

    return transaction

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        trade_option = request.form.get("Options")
        passphrase = request.form.get("passphrase")
        message = request.form.get("message")
        ticker = request.form.get("coinpair")
        entryprice = request.form.get("entryprice")
        stopprice = request.form.get("stopprice")

        # print(trade_option)
        print(request.form)

        data = {
            "passphrase": passphrase,
            "message":message,
            "ticker":ticker,
            "entryprice":float(entryprice),
            "stopprice":float(stopprice),
            "exchange":"BINANCE",
            "timestamp":"12:00",
            "origin":"TradingView"
        }   

        body = requests.post("http://127.0.0.1:5000/webhook", json=data)

        output = body.json()

        # print(output)

        return render_template("index.html", body=output)

    return render_template("index.html")

@app.route("/config", methods=["GET", "POST"])
def configuration():

    print (request.remote_addr)
    
    if request.method == "GET":

        print (f"Risk is {config.RISK}")
        print (f"Trading Mode is {config.TEST}")

        return render_template("config.html", a_risk=config.RISK, test=int(config.TEST))
    
    elif request.method == "POST":
        if request.remote_addr == "127.0.0.1":
            # if config.RISK != request.form["risk"]:
            #     config.RISK = request.form["risk"]

            # print(request.form.get("Options"))
            print(request.form["Options"])

        else: 
            # request.form.get("message")
            if config.RISK != request.form["risk"]:
                os.environ["RISK"] = request.form["risk"]

            if request.form["Options"] == "Test Mode":
                v_test = 1

            elif request.form["Options"] == "Dynamic Account Balance":
                v_test = 0

            elif request.form["Options"] == "Custom Account Balance":
                v_test = 2

            if config.TEST != v_test:
                os.environ["TEST"] = str(v_test)

            if v_test == 2:
                if config.TEST_ACCOUNT != request.form["Account Balance"]:
                    os.environ["TEST_ACCOUNT"] = request.form["Account Balance"]
            

    return render_template("config.html", a_risk=config.RISK, test=config.TEST)

@app.route('/webhook', methods=['POST'])
def webhook():
    #print(request.data)
    data = json.loads(request.data)

    if data['passphrase'] != config.WEBHOOK_PASSPHRASE:
        return{
            "code" : "error",
            "message" : "invalid Passphrase"
        }

    print(data['ticker'])
    print(data['message'])

    #Calculate Stop Loss
    SL = 1
    order_quantity = 0
    ac_position = 0
    body = ""
    subject = ""
    
    if data['message'] == "ENTRY LONG" or data['message'] == "ENTRY SHORT":
        SL = calculate_stop_loss(data)

        per_SL = "{:.2f}".format(SL * 100) + "%"

        per_Risk = "{:.2f}".format(config.RISK * 100) + "%"

        body = "SL : " + str(per_SL) + "\n"
        print("SL : " + str(per_SL))

        body = body + "\n"   #Add Line

        body = body + "Risk % : " + str(per_Risk) + "\n"
        print("Risk %  : " + str(per_Risk))
    
        body = body + "\n"   #Add Line

        #Get the current Account Balance
        account_btc, account_usdt = get_account_balance()
        body = body + "Account in BTC :" + str(account_btc) + "\n"
        body = body + "Account in USDT :" + str(account_usdt) + "\n"

        body = body + "\n"   #Add Line
        

        if config.TEST == 2:  #Force the position amount to TEST_ACCOUNT Amount
            account_btc = get_test_account_btc(account_usdt)
            print("Account in BTC: " + str(account_btc))
            body = body + "Account in BTC: " + str(account_btc) + "\n"

            account_usdt = config.TEST_ACCOUNT
            print("Account in USDT: " + str(account_usdt))
            body = body + "Account in USDT:" + str(account_usdt) + "\n"

            
        #Calculate the Position Size
        position, body = calc_position(data, account_btc, account_usdt, SL, body)

        #Get the USDT or BTC Balance
        if data['message'] == "ENTRY LONG":
            balance, asset = get_asset_balance(data)   #data['ticker'][-3:]
            body = body + "Coin Balance is: " + str(balance) + "\n"
            print(" Coin Balance is: " + str(balance))

            body = body + "\n"   #Add Line

            # #Check if Borrow is needed
            # if balance < position:
            
            #     borrow, body = borrow_asset(balance, position, asset, data, body)

            decimal, info = check_price_decimals(data['ticker'])
            ac_position = "{:0.0{}f}".format(position, decimal)


        elif data['message'] == "ENTRY SHORT":
            balance, asset = get_asset_balance(data)
            body = body + "Coin Balance is: " + str(balance) + "\n"
            print(" Coin Balance is: " + str(balance))

            decimal, info = check_price_decimals(data['ticker'])
            ac_position = "{:0.0{}f}".format(position, decimal)


    #Create the Order
    entry_price, order_id, body, subject = create_order(data, ac_position, body, "MARGIN_BUY")
    if entry_price:
        if data['message'] == "ENTRY LONG" or data['message'] == "ENTRY SHORT":
            body = body + "Entry Price is: " + str(entry_price) + "\n"
            print("Entry Price is: " + str(entry_price))

            #Get the Coins Quantity
            order_quantity = calc_coin_quantity(data, order_id)
            body = body + "Order Quantity is: " + str(order_quantity) + "\n"
            print ("Order Quantity is: " + str(order_quantity))

    #Create the Stop Lost for ENTRY Trades
    sl_side = " "
    sl_order_type = " "
    sl_price = 0
    sl_stopPrice = 0

    decimal, info = check_price_decimals(data['ticker'])

    if entry_price:
        if config.TEST != 1: 
            if data['message'] == "ENTRY LONG":
                print("ENTRY LONG Stop Loss")
                sl_side = SIDE_SELL
                sl_order_type = ORDER_TYPE_STOP_LOSS_LIMIT
                sl_pr = entry_price * ( 1 - SL)
                sl_stopPr = sl_pr * ( 1 + (SL*0.15))
                sl_price = "{:0.0{}f}".format(sl_pr, decimal)
                sl_stopPrice = "{:0.0{}f}".format(sl_stopPr, decimal)
                
                body = body + "Limit Price: " + sl_price + "\n"
                print("Limit Price: " + sl_price)
                body = body + "Stop Price: " + sl_stopPrice + "\n"
                print("Stop Price: " + sl_stopPrice)

                stop_lost_order, body = create_stop_lost(sl_side, order_quantity, data['ticker'], sl_order_type, sl_price, sl_stopPrice, body)
                 
                if stop_lost_order:
                     print("Stop Loss Order - Succes!")
                     body = body + "Stop Loss Order - Success!" + "\n"
                     subject = "Success!"

            elif data['message'] == "ENTRY SHORT":
                print("ENTRY SHORT Stop Loss")
                sl_side = SIDE_BUY
                sl_order_type = ORDER_TYPE_STOP_LOSS_LIMIT
                sl_pr = entry_price * ( 1 + SL)
                sl_stopPr = sl_pr * ( 1 - (SL*0.15))
                sl_price = "{:0.0{}f}".format(sl_pr, decimal)
                sl_stopPrice = "{:0.0{}f}".format(sl_stopPr, decimal)

                body = body + "Limit Price: " + sl_price + "\n"
                print("Limit Price: " + sl_price)
                body = body + "Stop Price: " + sl_stopPrice + "\n"
                print("Stop Price: " + sl_stopPrice)

                stop_lost_order, body = create_stop_lost(sl_side, order_quantity, data['ticker'], sl_order_type, sl_price, sl_stopPrice, body)

                if stop_lost_order:
                     print("Stop Loss Order - Succes!")
                     body = body + "Stop Loss Order - Success!" + "\n"
                     subject = "Success!"

    # create_email(data, body, subject)

    #END of Jim

    return jsonify(
        {
            "data" : body
        })