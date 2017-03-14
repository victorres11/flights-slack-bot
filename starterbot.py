import os
import time
import sys
import requests
from bs4 import BeautifulSoup
from collections import defaultdict
from IPython.core import ultratb
from slackclient import SlackClient


#sys.excepthook = ultratb.FormattedTB(mode='Verbose',
#             color_scheme='Linux', call_pdb=1)

# starterbot's ID as an environment variable
BOT_ID = os.environ.get("BOT_ID")

# constants
AT_BOT = "<@" + BOT_ID + ">"
EXAMPLE_COMMAND = "do"

# instantiate Slack & Twilio clients
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

# starterbot's ID as an environment variable
BOT_ID = os.environ.get("BOT_ID")

# constants
AT_BOT = "<@" + BOT_ID + ">"
EXAMPLE_COMMAND = "do"

# instantiate Slack & Twilio clients
slack_client = SlackClient(os.environ.get('SLACK_BOT_TOKEN'))

def handle_command(command, channel):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    response = "Not sure what you mean. Use the *" + EXAMPLE_COMMAND + \
               "* command with numbers, delimited by spaces."
    if command.startswith(EXAMPLE_COMMAND):
        response = "Not familiar with this command - if you want to check some cheap fares, message me `do flight check`"
        if command.find('flight') > -1:
            flight_data = get_flight_data()
            response = 'Here are some top fares I just found...\n\n'
            for flight_num, flight_datum in flight_data.iteritems():
                response += "Flight Deal {num}: JFK to {city} {price}\nwww.airfarewatchdog.com{link}\n\n".format(num=flight_num + 1, city=flight_datum['city'], price=flight_datum['price'], link=flight_datum['link'])

    slack_client.api_call("chat.postMessage", channel=channel,
                          text=response, as_user=True)

def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip().lower(), \
                       output['channel']
    return None, None

def get_flight_data():
    """ Will scrape the web page from airfarewatchdog.com (JFK only right now) and return
    the data we care about for printing in the slack channel (city, price, link).
    """
    # Turn top fares from GET request into parsable BeautifulSoup
    top_fares_results = requests.get('http://www.airfarewatchdog.com/cheap-flights/from-new-york-city-new-york/LGA/')
    top_fares_soup = BeautifulSoup(top_fares_results.text, 'html.parser')
    city_fare_rows = top_fares_soup.find_all(attrs={'class':'city_fare_row'})

    # Get the only pieces of data we care about to print later
    city_fare_row_dict = {}
    for num, city_fare_row in enumerate(city_fare_rows):
        # Just take the top ten to not overwhelm the slack channel.
        if num > 9:
            break
        city = city_fare_row.find(attrs={'class': 'city_fare__title_city'}).text
        price = city_fare_row.find(attrs={'class': 'city_fare__price_container-price'}).text
        link = city_fare_row.find(attrs={'class': 'city_fare__price_link'}).get('href')
        city_fare_row_dict[num] = { 'city' : city, 'price' : price, 'link' : link }
        
    return city_fare_row_dict


if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("StarterBot connected and running!")
        while True:
            command, channel = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                handle_command(command, channel)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")
