import RPi.GPIO as GPIO
import time
import serial
import requests
from datetime import datetime
import pytz

# Constants for pesticide calculation
alpha = 1.5
beta1 = 0.6
beta2 = 0.4
beta3 = 2.5
beta4 = 0.3
flow_rate = 27.78  # Average flow rate in ml/s (pesticide pump)
total_volume = 10.0  # Total water volume in ml

# GPIO pin for serial communication
TX_PIN = 14  # GPIO 14 (TX)

# Serial communication setup
ser = serial.Serial("/dev/serial0", 9600)  # Serial port for communication with Arduino

# GPIO setup
GPIO.setmode(GPIO.BCM)
GPIO.setup(TX_PIN, GPIO.OUT)

# Weather API Functions
def get_current_datetime():
    utc_now = datetime.now(pytz.utc)
    return utc_now.strftime("%Y-%m-%dT%H:%M:%SZ")

def get_current_location():
    try:
        response = requests.get("https://ipapi.co/json/")
        if response.status_code == 200:
            data = response.json()
            return {
                "latitude": data.get("latitude"),
                "longitude": data.get("longitude")
            }
        else:
            print(f"Error fetching location data: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request exception: {e}")
        return None

def get_weather_data(username, password, datetime_iso, latitude, longitude):
    parameters = "t_2m:C,precip_1h:mm"
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
    try:
        weather_info = {}
        weather_values = data.get('data', [])
        for item in weather_values:
            parameter = item.get('parameter')
            value = item.get('coordinates')[0].get('dates')[0].get('value')
            weather_info[parameter] = value
        return weather_info
    except (KeyError, IndexError, TypeError) as e:
        print(f"Error parsing weather data: {e}")
        return None

def calculate_pesticide_amount(precipitation, temperature, disease=1, age=5):
    pesticide_amount = alpha + (beta1 * precipitation) + (beta2 * temperature) + (beta3 * disease) + (beta4 * age)
    return min(pesticide_amount, total_volume)

def main():
    username = "none_n_swarna"
    password = "cXs0E3e2LQ"

    datetime_iso = get_current_datetime()
    location_data = get_current_location()

    if location_data:
        latitude = location_data['latitude']
        longitude = location_data['longitude']

        raw_weather_data = get_weather_data(username, password, datetime_iso, latitude, longitude)

        if raw_weather_data:
            weather_info = parse_weather_data(raw_weather_data)
            if weather_info:
                temperature = weather_info.get('t_2m:C')
                precipitation = weather_info.get('precip_1h:mm')

                pesticide_amount = calculate_pesticide_amount(precipitation, temperature)

                # Send pesticide amount to Arduino
                ser.write(f"{pesticide_amount}\n".encode('utf-8'))
                print(f"Pesticide Amount Sent: {pesticide_amount} ml")

    else:
        print("Failed to retrieve location data.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        GPIO.cleanup()
        ser.close()
