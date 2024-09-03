import os

def SendViaBluetooth():
    # Bluetooth address of the receiving device (your mobile phone)
    bd_addr = "44:16:FA:16:F6:FB"

    # Path to the image file
    image_path = "test.jpg"

    try:
        # Send the file using bluetooth-sendto
        os.system(f'bluetooth-sendto --device={bd_addr} {image_path}')
        print("Photo sent successfully via Bluetooth.")
    except Exception as e:
        print(f"Failed to send photo via Bluetooth: {e}")

# Send the photo via Bluetooth to your mobile phone
SendViaBluetooth()
