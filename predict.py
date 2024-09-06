import tensorflow as tf
import numpy as np
from PIL import Image

# Class labels for your model
class_labels = [
    "Tomato Septoria leaf spot", "Tomato mosaic virus", "Tomato Late blight", 
    "Tomato Spider mites (Two-spotted spider mite)", "Tomato Yellow Leaf Curl Virus", 
    "Tomato healthy", "Pepper bell Bacterial spot", "Potato healthy", 
    "Tomato Target Spot", "Tomato Leaf Mold", "Tomato Bacterial spot", 
    "Tomato Early blight", "Potato Late blight", "Potato Early blight", 
    "Pepper bell healthy"
]

# Step 1: Load the TensorFlow Lite model
interpreter = tf.lite.Interpreter(model_path="model.tflite")
interpreter.allocate_tensors()

# Step 2: Load and preprocess the image (assuming 'test.jpg' is in the same directory)
def preprocess_image(image_path, input_shape):
    image = Image.open(image_path).resize((input_shape[1], input_shape[2]))
    image = np.array(image).astype('float32') / 255.0  # Normalize the image
    image = np.expand_dims(image, axis=0)  # Add batch dimension
    return image

# Get input details
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Assuming the input shape is like [1, height, width, channels]
input_shape = input_details[0]['shape']
input_image = preprocess_image('test.jpg', input_shape)

# Step 3: Set the tensor to the input data
interpreter.set_tensor(input_details[0]['index'], input_image)

# Step 4: Run the model
interpreter.invoke()

# Step 5: Get the model output
output_data = interpreter.get_tensor(output_details[0]['index'])

# Step 6: Get the predicted class index and probability
predicted_class_idx = np.argmax(output_data, axis=1)[0]
predicted_probability = np.max(output_data)

# Step 7: Apply threshold of 0.7 and output the result
threshold = 0.7
if predicted_probability > threshold:
    predicted_class = class_labels[predicted_class_idx]
    print(f"Predicted Class: {predicted_class} with confidence {predicted_probability:.2f}")
else:
    print(f"No confident prediction. Highest probability: {predicted_probability:.2f}")
