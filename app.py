import requests
import xml.etree.ElementTree as ET
import openai
import random
import re
import os
import csv
import datetime
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Load credentials from secrets file
credentials = json.loads(os.environ['SECRETS'])

# Set up Google Sheets API credentials
creds = service_account.Credentials.from_service_account_info(credentials, scopes=['https://www.googleapis.com/auth/spreadsheets'])
sheets_api = build('sheets', 'v4', credentials=creds)

# Set up OpenAI API credentials
openai.api_key = credentials['openai_key']
MODEL_TYPE = 'gpt-3.5-turbo'

# Define list of Irish figures to randomly select from
irish_figures = [ 
    'Bryan Mills (liam neeson) from Taken',
    'James Joyce',
    'Oscar Wilde',
    'Samuel Beckett',
    'W.B. Yeats',
    'Seamus Heaney',
    'Patrick Kavanagh',
    'Conor Mcgregor',
    'Bryan Mills (Liam neeson) from Taken',
    'Michael D. Higgins',
    'Brendan Gleeson',
    'Hozier',
    'Seamus Heaney',
    'C.S. Lewis',
    'Nidge from Love/Hate'
]


# Randomly select an Irish figure
selected_figure = irish_figures[random.randint(0, len(irish_figures)-1)]

# define a function
def format_location(lat, long):
    return {'lat': str(lat), 'long': str(long)}

# Function to get weather data from API
def get_weather_data(lat, long):
    url = 'http://metwdb-openaccess.ichec.ie/metno-wdb2ts/locationforecast'
    response = requests.get(url, params=format_location(lat, long))
    return ET.fromstring(response.content)

def bucket_cloudiness(percent):
    if percent == 0:
        return "clear"
    elif percent == 100:
        return "overcast"
    elif int(percent) <= 25:
        return "mostly clear"
    elif int(percent) <= 75:
        return "partly cloudy"
    else:
        return "mostly cloudy"
    
def bucket_pressure(pressure):
    if pressure <= 1000:
        return "very low pressure"
    elif pressure <= 1010:
        return "low pressure"
    elif pressure <= 1020:
        return "moderate pressure"
    elif pressure <= 1030:
        return "high pressure"
    else:
        return "very high pressure"
    
    
def bucket_humidity(humidity):
    if humidity < 30:
        return "very dry"
    elif humidity < 60:
        return "moderately humid"
    else:
        return "very humid"
    
def wind_direction_description(abbreviation):
    direction_map = {
        'N': 'Northerly',
        'NE': 'North Easterly',
        'E': 'Easterly',
        'SE': 'South Easterly',
        'S': 'Southerly',
        'SW': 'South Westerly',
        'W': 'Westerly',
        'NW': 'North Westerly'
    }
    return direction_map.get(abbreviation, '')

# Function to parse weather data
def parse_weather_data(root):
    forecast_time = root.find('.//time').attrib['from']
    day_of_week = forecast_time.split('T')[0]
    temperature = root.findall('.//temperature')[-1].attrib['value']
    wind_direction = root.findall('.//windDirection')[-1].attrib['name']
    wind_speed = root.findall('.//windSpeed')[-1].attrib['name']
    cloudiness = root.findall('.//cloudiness')[-1].attrib['percent']
    cloudiness_int = float(cloudiness)
    humidity = root.findall('.//humidity')[-1].attrib['value']
    humidity_int = float(humidity)
    pressure = root.findall('.//pressure')[-1].attrib['value']
    pressure_int = float(pressure)

    return {
        'day_of_week': day_of_week,
        'temperature': temperature,
        'wind_direction': wind_direction,
        'wind_speed': wind_speed,
        'cloudiness': cloudiness_int,
        'humidity': humidity_int,
        'pressure': pressure_int
    }

# Your existing bucketing functions for cloudiness, pressure, and humidity

def truncate_to_last_sentence(text, max_chars):
    text = text[:max_chars]
    last_sentence_end = max([m.start() for m in re.finditer(r"[.!?]", text)] + [0])
    return text[:last_sentence_end + 1].strip()

# assign prompt
prompt = f"Describe the weather in the style of {selected_figure}. Don't say who you are! Factual, funny & witty. 270 char max."

# Function to generate tweet
def generate_tweet(weather_data, city):
    weather_info = [
        city,
        f"Date: {weather_data['day_of_week']}",
        f"Temperature: Highest temperatures of {weather_data['temperature']}°C",
        f"Wind: {wind_direction_description(weather_data['wind_direction']).lower()} winds ({weather_data['wind_speed']})",
        f"Cloudiness: {bucket_cloudiness(weather_data['cloudiness'])}",
        f"Humidity: {bucket_humidity(weather_data['humidity'])}",
        f"Pressure: {bucket_pressure(weather_data['pressure'])}"
    ]

    weather_str = "\n".join(weather_info)

    # Call OpenAI API to generate response
    response = openai.ChatCompletion.create(
        model=MODEL_TYPE,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": weather_str},
        ],
        max_tokens=100
    )

    # Truncate the response to the last complete sentence within 270 characters
    truncated_response = truncate_to_last_sentence(response.choices[0]['message']['content'].strip(), 260)

    # Format and return the generated tweet
    tweet = truncated_response + f"\n#{city.replace(' ', '')}Weather #WhoamI"
    return tweet, response

# Function to append values to Google Sheet
def append_values_to_sheet(sheet_id, range_name, values):
    try:
        sheets_api.spreadsheets().values().append(
            spreadsheetId=sheet_id,
            range=range_name,
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body={'values': [values]}
        ).execute()
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None

# Function to process a county
def process_county(lat, long, city):
    weather_data = get_weather_data(lat, long)
    parsed_weather_data = parse_weather_data(weather_data)
    tweet, response = generate_tweet(parsed_weather_data, city)

    timestamp_tweet_created_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    lat_long_str = str(format_location(lat, long))

    append_values_to_sheet(sheet_id, 'Tweets!A2:P', [
        timestamp_tweet_created_at,
        parsed_weather_data['day_of_week'],
        parsed_weather_data['temperature'],
        lat_long_str,
        city,
        wind_direction_description(parsed_weather_data['wind_direction']),
        parsed_weather_data['wind_speed'],
        parsed_weather_data['cloudiness'],
        parsed_weather_data['humidity'],
        parsed_weather_data['pressure'],
        response['usage']['prompt_tokens'],
        response['usage']['completion_tokens'],
        len(prompt),
        len(response.choices[0]['message']['content'].strip()),
        len(tweet),
        tweet
    ])
# Function to process all counties
def process_all_counties(filename):
    with open(filename, mode='r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['Flag'] == '1':
                lat = float(row['lat'])
                long = float(row['lng'])
                city = row['city']
                process_county(lat, long, city)

# Call the function to process all counties
process_all_counties('counties.csv')
