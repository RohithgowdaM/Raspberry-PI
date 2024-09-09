import RPi.GPIO as GPIO
import time
import requests
import subprocess
import numpy as np
import tensorflow as tf
from datetime import datetime
import pytz
from pushbullet import Pushbullet

# Constants for pesticide calculation
alpha = 1.5
beta1 = 0.6
beta2 = 0.4
beta3 = 2.5
beta4 = 0.3
total_volume = 10.0  # Total pesticide volume in ml
motor_capacity_lph = 3600.0  # Motor capacity in liters per hour

# Extra pesticide amount based on model predictions
EXTRA_PESTICIDE_PER_DISEASE = {
    "Tomato Septoria leaf spot": 0.5,
    "Tomato mosaic virus": 0.7,
    "Tomato Late blight": 0.6,
    "Tomato Spider mites (Two-spotted spider mite)": 0.4,
    "Tomato Yellow Leaf Curl Virus": 0.5,
    "default": 0.3
}

class_labels = [
    "Tomato Septoria leaf spot", "Tomato mosaic virus", "Tomato Late blight", 
    "Tomato Spider mites (Two-spotted spider mite)", "Tomato Yellow Leaf Curl Virus", 
    "Tomato healthy", "Pepper bell Bacterial spot", "Potato healthy", 
    "Tomato Target Spot", "Tomato Leaf Mold", "Tomato Bacterial spot", 
    "Tomato Early blight", "Potato Late blight", "Potato Early blight", 
    "Pepper bell healthy"
]

# GPIO pin for controlling the motor
MOTOR_PIN = 18  # Ensure MOTOR_PIN is correctly set

# GPIO setup
def setup_gpio():
    GPIO.cleanup()  # Reset GPIO states
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(MOTOR_PIN, GPIO.OUT)
    GPIO.output(MOTOR_PIN, GPIO.LOW)  # Make sure the motor is off initially
    print(f"Setup complete. Motor pin {MOTOR_PIN} is LOW.")

def capture_image():
    """Capture image from camera."""
    print("Capturing Image:")
    result = subprocess.run(['libcamera-still', '-o', 'testimage.jpg'])
    if result.returncode == 0:
        print("Image captured successfully")
        return 'testimage.jpg'
    else:
        print("Failed to capture image")
        return None

def load_model():
    """Load TFLite model."""
    interpreter = tf.lite.Interpreter(model_path="model.tflite")
    interpreter.allocate_tensors()
    return interpreter

def predict_disease(interpreter, image_path):
    """Run model inference to predict plant disease."""
    img = tf.io.read_file(image_path)
    img = tf.image.decode_jpeg(img, channels=3)
    img = tf.image.resize(img, [256, 256])
    img = tf.cast(img, tf.float32) / 255.0
    img = np.expand_dims(img, axis=0)

    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    interpreter.set_tensor(input_details[0]['index'], img)
    interpreter.invoke()

    output_data = interpreter.get_tensor(output_details[0]['index'])[0]
    predicted_index = np.argmax(output_data)
    predicted_class = class_labels[predicted_index]
    probability = output_data[predicted_index]

    return predicted_class, probability

def calculate_base_pesticide_amount(precipitation, temperature, disease=1, age=5):
    """Calculate base pesticide amount based on weather data."""
    return alpha + (beta1 * precipitation) + (beta2 * temperature) + (beta3 * disease) + (beta4 * age)

def calculate_total_pesticide_amount(base_amount, disease_class, probability):
    """Calculate total pesticide amount based on model predictions."""
    if probability >= 0.7:
        extra_amount = EXTRA_PESTICIDE_PER_DISEASE.get(disease_class, EXTRA_PESTICIDE_PER_DISEASE["default"])
        return min(base_amount + extra_amount, total_volume)
    else:
        return base_amount

def pump_pesticide(amount):
    """Activate motor to pump the calculated amount of pesticide."""
    runtime = (amount / motor_capacity_lph) * 3600  # Convert liters/hour to seconds
    print(f"Pumping pesticide for {runtime:.2f} seconds")

    GPIO.output(MOTOR_PIN, GPIO.HIGH)
    print(f"Motor pin {MOTOR_PIN} set to HIGH")
    time.sleep(runtime)
    GPIO.output(MOTOR_PIN, GPIO.LOW)
    print("Pumping complete. Motor pin LOW.")

def send_notification():
    """Send a notification with the image via Pushbullet."""
    pb = Pushbullet("o.uHNqiT66XGLVc50DxBoyUf9DQILCfdfr")
    with open('testimage.jpg', 'rb') as pic:
        file_data = pb.upload_file(pic, "Plant Picture.jpg")
        pb.push_file(**file_data)

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
        response = requests.get(endpoint, auth=(username, password), timeout=5)
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

def main():
    username = "none_n_swarna"
    password = "cXs0E3e2LQ"

    # Setup GPIO
    setup_gpio()

    # Load the model
    interpreter = load_model()

    # Get the current datetime and location
    datetime_iso = get_current_datetime()
    location_data = get_current_location()

    # Fetch weather data once
    if location_data:
        latitude = location_data['latitude']
        longitude = location_data['longitude']

        raw_weather_data = get_weather_data(username, password, datetime_iso, latitude, longitude)
        if raw_weather_data:
            weather_info = parse_weather_data(raw_weather_data)
            if weather_info:
                temperature = float(weather_info.get('t_2m:C', 25))  # Default to 25°C
                precipitation = float(weather_info.get('precip_1h:mm', 0))  # Default to 0 mm
            else:
                temperature = 25.0  # Hardcoded fallback temperature
                precipitation = 0.0  # Hardcoded fallback precipitation
        else:
            temperature = 25.0  # Hardcoded fallback temperature
            precipitation = 0.0  # Hardcoded fallback precipitation

        base_pesticide_amount = calculate_base_pesticide_amount(precipitation, temperature)

        while True:
            # Capture image
            image_path = capture_image()
            if image_path:
                # Predict disease
                disease_class, probability = predict_disease(interpreter, image_path)
                print(f"Detected: {disease_class} with probability {probability:.2f}")

                # Calculate total pesticide amount
                total_pesticide_amount = calculate_total_pesticide_amount(base_pesticide_amount, disease_class, probability)
                print(f"Total Pesticide Amount: {total_pesticide_amount} ml")

                # Pump pesticide
                pump_pesticide(total_pesticide_amount)

                # Send image and notification
                send_notification()

            # Wait for 20 seconds before the next cycle
            time.sleep(20)

    else:
        print("Failed to retrieve location data.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        GPIO.cleanup()
        print("Program terminated.")
