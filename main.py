import os
import requests
import smtplib
from _datetime import datetime

# Sheety API
SHEETY_URL = os.environ.get("SHEETY_URL")
SHEETY_AUTHORIZATION_HEADER = os.environ.get("SHEETY_AUTHORIZATION_HEADER")
SHEETY_HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {SHEETY_AUTHORIZATION_HEADER}",
}
# Tequila API
TEQUILA_URL = os.environ.get("TEQUILA_URL")
TEQUILA_API_KEY = os.environ.get("TEQUILA_API_KEY")
TEQUILA_HEADERS = {"apikey": TEQUILA_API_KEY}
# SMTP
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")
# SPREADSHEET LINK
SPREADSHEET_URL = os.environ.get("SPREADSHEET_URL")

# Pull flight data using Tequila API
def find_data(iata_code):
    params = {
        "fly_from": "SNA",
        "fly_to": iata_code,
        "date_from": datetime.now().strftime('%d/%m/%Y'),
        "date_to": "31/12/2024",
        "nights_in_dst_from": 3,
        "nights_in_dst_to": 7,
        "flight_type": "round",
        "adults": 2,
        "max_stopovers": 2,
        "curr": "USD",
        "limit": 100,
        "sort": "price",
    }
    response = requests.get(url=TEQUILA_URL, headers=TEQUILA_HEADERS, params=params)
    return response.json()['data'][0]


# Pull database flight prices stored in Google Sheet
response = requests.get(url=SHEETY_URL, headers=SHEETY_HEADERS)
response_json = response.json()['prices']
prices = {}
row_no = 2
for i in response_json:
    prices[i['city']] = [i['iataCode'], int(i['lowestPrice']), row_no]
    row_no += 1
print(prices)

# Pull current flight prices using Tequila api
lower_price = False
for i in prices:
    new_price = find_data(prices[i][0])['price']
    old_price = prices[i][1]
    link = find_data(prices[i][0])['deep_link']
    # Compare current and database flight prices
    if new_price < old_price:
        print(f"Lower price for {i} flight found! The price was {old_price} and is now {new_price}.")
        # Update database flight price to lower price
        requests.put(url=f"{SHEETY_URL}/prices[i][2]", headers=SHEETY_HEADERS, json={"price": {"lowestPrice": new_price}})
        requests.put(url=f"{SHEETY_URL}/prices[i][2]", headers=SHEETY_HEADERS, json={"price": {"link": link}})
        lower_price = True
    else:
        print(f"No lower price for {i} found")

# Send email notification
with smtplib.SMTP("smtp.gmail.com", 587) as cx:
    cx.starttls()
    cx.login(user=SENDER_EMAIL, password=SENDER_PASSWORD)
    if lower_price:
        cx.sendmail(from_addr=SENDER_EMAIL,
                    to_addrs=RECEIVER_EMAIL,
                    msg=f"From: {SENDER_EMAIL}\r\nTo: {RECEIVER_EMAIL}\r\nSubject: Flight Deals\r\n\r\nLower prices found! Here are the updated prices: {str(prices)}\r\nCheck the spreadsheet for updated links.\r\n{SPREADSHEET_URL}")
    else:
        cx.sendmail(from_addr=SENDER_EMAIL,
                    to_addrs=RECEIVER_EMAIL,
                    msg=f"From: {SENDER_EMAIL}\r\nTo: {RECEIVER_EMAIL}\r\nSubject: Flight Deals\r\n\r\nNo lower prices found. Check the spreadsheet for current prices.\r\n{SPREADSHEET_URL}")
