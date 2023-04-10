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

sheet_id = "10aq42tgz4bjAORAYSykXAy1PGZRGN2pr_gSb1ai79cg"

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
    'Seamus Heaney',
    'C.S. Lewis',
    "Father Ted"
]

def random_art_style():
    art_styles = [
        "Surrealism",
        "Abstract Expressionism",
        "Impressionism",
        "Post-Impressionism",
        "Expressionism",
        "Fauvism",
        "Cubism",
        "Pop Art",
        "Dadaism",
        "Futurism",
        "Minimalism",
        "Realism",
        "Romanticism",
        "Baroque",
        "Rococo",
        "Neoclassicism",
        "Byzantine",
        "Gothic",
        "Renaissance",
        "Mannerism"
    ]
    return random.choice(art_styles)


# Randomly select an Irish figure
selected_figure = irish_figures[random.randint(0, len(irish_figures)-1)]

# Randomly select an Art Style
selected_art_style = random_art_style()

# define a function for lat and long
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
    return tweet, response, truncated_response
    

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

def image_cost_calc(image_size):
    cost_per_image = {
        '1024x1024': 0.020,
        '512x512': 0.018,
        '256x256': 0.016,
    }
    
    if image_size in cost_per_image:
        return cost_per_image[image_size]
    else:
        raise ValueError(f"Invalid image size: {image_size}")

def generate_dalle_prompt(truncated_response, city, selected_art_style):
    prompt = f"Generate a descriptive DALL-E image prompt/description for a {selected_art_style} artwork of {city} based on the following weather description:"

    prompt_response = openai.ChatCompletion.create(
        model=MODEL_TYPE,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": truncated_response},
        ],
        max_tokens=100
    )
    
    dall_e_prompt = prompt_response.choices[0].message['content'].strip()
    return dall_e_prompt, prompt_response

def generate_dalle_image(prompt):
    size="256x256"
    response = openai.Image.create(
        prompt=prompt,
        n=1,
        size=size
    )

    image_cost = image_cost_calc(size)
    dalle_image_url = response['data'][0]['url']
    return dalle_image_url, image_cost


# Function to process a county
def process_county(lat, long, city):
    weather_data = get_weather_data(lat, long)
    parsed_weather_data = parse_weather_data(weather_data)
    tweet, response, truncated_response = generate_tweet(parsed_weather_data, city)

    # Generate the DALL-E prompt using the truncated response
    dall_e_prompt, prompt_response = generate_dalle_prompt(truncated_response, city, selected_art_style)

    # Generate the DALL-E image using the generated prompt
    dalle_image_url, image_cost = generate_dalle_image(dall_e_prompt)

    timestamp_tweet_created_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    lat_long_str = str(format_location(lat, long))


    append_values_to_sheet(sheet_id, 'Tweets!A2:P', [
        timestamp_tweet_created_at,
        parsed_weather_data['day_of_week'],
        parsed_weather_data['temperature'],
        lat_long_str,
        city,
        dalle_image_url,
        selected_figure,
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
        tweet,
        selected_art_style,
        dall_e_prompt,
        image_cost,
        prompt_response['usage']['prompt_tokens'],
        prompt_response['usage']['completion_tokens'],
        len(dall_e_prompt),
        len(prompt_response.choices[0]['message']['content'].strip())
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
