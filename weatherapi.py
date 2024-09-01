import requests
from datetime import datetime
import pytz

def get_current_datetime():
    """
    Get the current UTC date and time.
    """
    utc_now = datetime.now(pytz.utc)
    formatted_datetime = utc_now.strftime("%Y-%m-%dT%H:%M:%SZ")
    return formatted_datetime

def get_current_location():
    """
    Get the current location based on IP address using a geolocation API.
    """
    try:
        response = requests.get("https://ipapi.co/json/")
        if response.status_code == 200:
            data = response.json()
            latitude = data.get("latitude")
            longitude = data.get("longitude")
            city = data.get("city")
            region = data.get("region")
            country = data.get("country_name")
            return {
                "latitude": latitude,
                "longitude": longitude,
                "city": city,
                "region": region,
                "country": country
            }
        else:
            print(f"Error fetching location data: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request exception: {e}")
        return None

def get_weather_data(username, password, datetime_iso, latitude, longitude):
    """
    Fetch weather data from Meteomatics API for the given datetime and location.
    """
    parameters = (
        "t_2m:C,"           # Temperature at 2 meters [°C]
        "precip_1h:mm,"     # Precipitation in the last hour [mm]
        "precip_24h:mm"     # Precipitation in the last 24 hours [mm]
    )
    
    location = f"{latitude},{longitude}"
    endpoint = f"https://api.meteomatics.com/{datetime_iso}/{parameters}/{location}/json"
    
    try:
        response = requests.get(endpoint, auth=(username, password))
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching weather data: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request exception: {e}")
        return None

def parse_weather_data(data):
    """
    Parse and format the weather data for display.
    """
    try:
        weather_values = data.get('data', [])
        weather_info = {}
        for item in weather_values:
            parameter = item.get('parameter')
            value = item.get('coordinates')[0].get('dates')[0].get('value')
            weather_info[parameter] = value
        return weather_info
    except (KeyError, IndexError, TypeError) as e:
        print(f"Error parsing weather data: {e}")
        return None

def main():
    username = "none_n_swarna"
    password = "cXs0E3e2LQ"
    
    datetime_iso = get_current_datetime()
    location_data = get_current_location()
    
    if location_data:
        latitude = location_data['latitude']
        longitude = location_data['longitude']
        print(f"Fetching weather data for {location_data['city']}, {location_data['region']}, {location_data['country']} at {datetime_iso}")
        
        raw_weather_data = get_weather_data(username, password, datetime_iso, latitude, longitude)
        
        if raw_weather_data:
            weather_info = parse_weather_data(raw_weather_data)
            if weather_info:
                print("\nCurrent Weather Data:")
                print(f"Temperature: {weather_info.get('t_2m:C')} °C")
                print(f"Precipitation (last hour): {weather_info.get('precip_1h:mm')} mm")
                print(f"Precipitation (last 24 hours): {weather_info.get('precip_24h:mm')} mm")
            else:
                print("Failed to parse weather data.")
        else:
            print("Failed to retrieve weather data.")
    else:
        print("Failed to retrieve location data.")

if __name__ == "__main__":
    main()
