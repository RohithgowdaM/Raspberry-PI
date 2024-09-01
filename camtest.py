import subprocess
from pushbullet import Pushbullet
from tkinter import messagebox
from tkinter import *

def CaptureImage():
    print("Capturing Image:")
    # Use subprocess to call libcamera-still
    result = subprocess.run(['libcamera-still', '-o', 'testimage.jpg'])
    if result.returncode == 0:
        print("Image captured successfully")
    else:
        print("Failed to capture image")

def SendNotification():
    root = Tk()
    root.geometry("200x100")
    root.withdraw()  # Hide the main Tkinter window

    # Replace with your actual Pushbullet API key
    pb = Pushbullet("o.uHNqiT66XGLVc50DxBoyUf9DQILCfdfr")
    
    with open('testimage.jpg', 'rb') as pic:
        file_data = pb.upload_file(pic, "Picture.jpg")
        push = pb.push_file(**file_data)
        
        if push['active']:
            messagebox.showinfo("Notification", "Message sent successfully.")
        else:
            messagebox.showwarning("Warning", "Sending message failed.")
    
    root.destroy()

# Capture the image using libcamera-still
CaptureImage()

# Send the notification
SendNotification()
