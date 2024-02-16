# Weather-Inspired Tweet & Image Generator

## Features
- Random selection of Irish literary figures & art styles.
- Fetches weather data for specified locations.
- Generates tweets using OpenAI in the style of selected figures.
- Creates images with DALL-E based on tweets.
- Logs data in Google Sheets.

## Components
- **API Setup:** Google Sheets, OpenAI.
- **Utility Functions:** Data handling, art style selection.
- **Main Functions:** Fetch & parse weather data, generate tweet & image, log data.

## Execution
1. Set API credentials and prepare `counties.csv`.
2. Install required Python modules.
3. Run with `process_all_counties('counties.csv')`.
