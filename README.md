﻿# gaelicgales

Weather-Inspired Artistic Tweet Generator
This program generates weather-inspired tweets in the style of notable Irish literary figures and accompanies the tweet with a DALL-E generated image.

Features:
Random Selection of Literary Figures: The program randomly chooses a prominent Irish literary figure from a predefined list.
Random Selection of Art Style: The program also randomly selects an art style for the DALL-E generated image.
Weather Data Collection: The program fetches weather data for a given latitude and longitude.
Tweet Generation: Using the OpenAI API, the program takes the weather data and crafts a tweet in the style of the chosen literary figure.
DALL-E Image Generation: The program also generates an image inspired by the tweet using OpenAI's DALL-E.
Google Sheets Integration: The program appends the generated tweets, the selected literary figure, DALL-E image URLs, and other related data to a specified Google Sheet.
Modules and Functions:
Initialization and API Set-up:
API credentials are loaded from a secrets file.
Set up for Google Sheets API and OpenAI API.
Utility Functions:
Several functions like random_art_style, format_location, translate_beaufort_wind_scale_norwegian_to_english, etc., provide utility operations.
Bucketing functions like bucket_cloudiness, bucket_pressure, bucket_humidity to categorize weather parameters into descriptive categories.
truncate_to_last_sentence: Truncates text to the last full sentence within a specified character limit.
Weather Data Handling:
get_weather_data: Fetches weather data for a given latitude and longitude.
parse_weather_data: Parses the fetched weather data.
Tweet and Image Generation:
generate_tweet: Crafts a tweet in the style of a selected Irish figure using OpenAI.
generate_dalle_prompt: Creates a prompt for DALL-E based on the generated tweet.
generate_dalle_image: Generates an image using DALL-E.
Google Sheets Operations:
append_values_to_sheet: Appends data to a specified range in a Google Sheet.
Processing Functions:
process_county: Orchestrates the entire process for a single county (fetching weather data, generating tweet, generating image, and appending to Google Sheet).
process_all_counties: Iterates over all counties (from a CSV file) and processes them.
How to Run:
To execute this program:

Ensure you have a counties.csv file with the required structure.
Load your API credentials for Google Sheets and OpenAI into an environment variable named SECRETS.
Run the main function process_all_counties('counties.csv').
Note:
Make sure you have the necessary modules installed using pip (requests, openai, google-auth, google-auth-httplib2, google-api-python-client) and have appropriate permissions set up for the Google Sheets API.

This README provides an overview of the code's functionalities and how to execute it. Adjustments can be made based on any additional context or specific instructions you'd like to include!
