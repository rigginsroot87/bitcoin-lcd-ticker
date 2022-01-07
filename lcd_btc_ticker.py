# Created 06/09/2018 by reddit user anonananananabatman
# Made available under GNU GENERAL PRIVATE LICENSE
# Modified by Jeremiah Root
# ver 1.0
import time
import json
import requests
import I2C_LCD_driver
import datetime
import pandas as pd
import asyncio
from bitcoinrpc import BitcoinRPC

#define get connection count, needs await asyncio stuff so the program can await a response from bitcoin core
#shit error handling
async def get_num_conns():
    try:
        async with BitcoinRPC("http://localhost:8332", "rpcuser", "rpcpassword") as rpc:
            return await rpc.getconnectioncount()
    except:
        return -1
#define get numblocks, needs await asyncio stuff so the program can await a response from bitcoin core
#shit error handling
async def get_num_blocks():
    try:
        async with BitcoinRPC("http://localhost:8332", "rpcuser", "rpcpassword") as rpc:
            return await rpc.getblockcount()
    except:
        return -1
#initiate screen
mylcd = I2C_LCD_driver.lcd()
# countdown1 = 240
# while countdown1 >= 0:
#     if countdown1 >= 10:
#         mylcd.lcd_display_string_pos("Starting in T-"+str(countdown1),1,1)
#     else:
#         mylcd.lcd_display_string_pos("Starting in T-0"+str(countdown1),1,1)
# 
#     countdown1 = countdown1-1
#     time.sleep(1)

def load_price_vars():
    #get 24 hour prices, block height, times from api, put in pandas df, calculate price change over the last day, return it all as strings
    #shit error handling
    try:
        raw_block_h = requests.get('https://blockchain.info/q/getblockcount')
        current_height = format(json.loads(raw_block_h.text),",")
        b = requests.get('https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=1&interval=hourly')
        priceFloat = json.loads(b.text)['prices']
        prices = pd.DataFrame(priceFloat, columns = ['date','price'])
        prices['date']=prices['date'].apply(lambda d: datetime.datetime.fromtimestamp(int(d)/1000).strftime('%Y-%m-%d %H:%M'))

        start_price = prices.iloc[0,1]

        prices['perc_change'] = prices['price']/start_price - 1
        current_time = prices.iloc[-1,0]
        current_price = "$"+ format(round(prices.iloc[-1,1]),',')
        perc_24_hr_change = str(format(prices.iloc[-1,2]*100,".1g"))+'%'

        
        
        return current_time, current_price, perc_24_hr_change, current_height
    except requests.ConnectionError:
        return "-1","-1","-1","-1"
    
while True:
    #define on/off hours
    now = datetime.datetime.now()
    wakeup_time = now.replace(hour=5, minute=4, second=20, microsecond=69)
    sleep_time = now.replace(hour=20, minute=4, second=20, microsecond=69)
    #if during waking hours run the display program
    if wakeup_time <= now <= sleep_time:
        numblocksnode = asyncio.run(get_num_blocks())
        numconnsnode = asyncio.run(get_num_conns())
        mylcd.lcd_clear()
        curr_time, curr_price, curr_perc_change, curr_height = load_price_vars()

        mylcd.lcd_write(0x80)
        mylcd.lcd_display_string(curr_price + "/BTC", 1)
        mylcd.lcd_display_string("24 HR CHG: " + curr_perc_change , 2)
        mylcd.lcd_display_string(curr_time, 3)
        whitefill = 8 - len(format(numblocksnode,",")) 
        mylcd.lcd_display_string("BLK HT NDE: " + format(numblocksnode,",") + " "*whitefill , 4)
        #mylcd.lcd_display_string_pos(("%s" %time.strftime("%I:%M:%S%p")) + (" %s" %time.strftime("%m/%d")), 3, 0)
        countdown = 99
        #cycle through different info during countdown
        while countdown >= 0:
            if countdown % 16 > 10:
              
                mylcd.lcd_display_string("BLK HT WEB: " + curr_height + " " , 4)

            elif countdown % 16 > 5:
                whitefill = 3 - len(str(numconnsnode)) 
                mylcd.lcd_display_string("CONNECTIONS NDE: " + str(numconnsnode) + " "*whitefill, 4)
            else:
                whitefill = 8 - len(format(numblocksnode,",")) 
                mylcd.lcd_display_string("BLK HT NDE: " + format(numblocksnode,",") + " "*whitefill , 4)
                
            if countdown >= 10:
                mylcd.lcd_display_string_pos("T-"+str(countdown),1,16)
            else:
                mylcd.lcd_display_string_pos("T-0"+str(countdown),1,16)

            countdown = countdown-1
            time.sleep(1)
    #otherwise we want it off, don't run the ticker, turn off the light and check if it's time to be awake every 2 min
    else:
        mylcd.backlight(0)
        time.sleep(120)
