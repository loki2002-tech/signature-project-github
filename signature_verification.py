import tkinter as tk
from tkinter.filedialog import askopenfilename
from tkinter import messagebox
import os
import cv2
from cryptography.fernet import Fernet
from skimage.metrics import structural_similarity as ssim

# Constants
THRESHOLD = 80
KEY_FILE = "encryption.key"

# Load or generate the encryption key
if os.path.exists(KEY_FILE):
    with open(KEY_FILE, 'rb') as keyfile:
        KEY = keyfile.read()
else:
    KEY = Fernet.generate_key()
    with open(KEY_FILE, 'wb') as keyfile:
        keyfile.write(KEY)

cipher_suite = Fernet(KEY)

# Utility Functions
def browsefunc(ent):
    filename = askopenfilename(filetypes=[("Image Files", "*.jpeg;*.png;*.jpg")])
    if filename:
        ent.delete(0, tk.END)
        ent.insert(tk.END, filename)
        encrypt_image(filename)  # Automatically encrypt the selected image

def capture_image_from_cam_into_temp(sign=1):
    cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cv2.namedWindow("Capture Image")
    while True:
        ret, frame = cam.read()
        if not ret:
            print("Failed to grab frame")
            break
        cv2.imshow("Capture Image", frame)
        k = cv2.waitKey(1)
        if k % 256 == 27:  # ESC pressed
            print("Escape hit, closing...")
            break
        elif k % 256 == 32:  # SPACE pressed
            if not os.path.isdir('temp'):
                os.mkdir('temp', mode=0o777)
            img_name = f"./temp/test_img{sign}.png"
            cv2.imwrite(filename=img_name, img=frame)
            print(f"{img_name} written!")
            encrypt_image(img_name)  # Automatically encrypt the captured image
            break
    cam.release()
    cv2.destroyAllWindows()
    return True

def capture_image(ent, sign=1):
    filename = os.path.join(os.getcwd(), f"temp/test_img{sign}.png")
    res = messagebox.askquestion('Click Picture', 'Press Space Bar to capture and ESC to exit')
    if res == 'yes':
        capture_image_from_cam_into_temp(sign=sign)
        ent.delete(0, tk.END)
        ent.insert(tk.END, filename)
    return True

# Encryption and Decryption Functions
def encrypt_image(path):
    try:
        with open(path, 'rb') as file:
            data = file.read()
        encrypted_data = cipher_suite.encrypt(data)
        with open(path, 'wb') as file:
            file.write(encrypted_data)
    except Exception as e:
        print(f"Error encrypting file {path}: {e}")

def decrypt_image(path):
    try:
        with open(path, 'rb') as file:
            encrypted_data = file.read()
        decrypted_data = cipher_suite.decrypt(encrypted_data)
        with open(path, 'wb') as file:
            file.write(decrypted_data)
    except Exception as e:
        raise ValueError(f"Error decrypting file {path}: {e}")

# Image Comparison Function
def compare_images(path1, path2):
    """Compares two images and returns similarity percentage."""
    img1 = cv2.imread(path1, cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread(path2, cv2.IMREAD_GRAYSCALE)
    img1 = cv2.resize(img1, (300, 300))
    img2 = cv2.resize(img2, (300, 300))
    similarity_value = ssim(img1, img2) * 100
    return similarity_value

# Main Function for Checking Similarity
def check_similarity(window, path1, path2):
    """Compares two signatures and displays the result."""
    if not os.path.exists(path1) or not os.path.exists(path2):
        messagebox.showerror("Error", "One or both signature images are missing!")
        return

    try:
        # Decrypt images for comparison
        decrypt_image(path1)
        decrypt_image(path2)

        similarity = compare_images(path1, path2)

        # Re-encrypt images for security
        encrypt_image(path1)
        encrypt_image(path2)

        if similarity >= THRESHOLD:
            messagebox.showinfo("Success", f"Signatures Match ({similarity:.2f}% similar)!")
        else:
            messagebox.showerror("Failure", f"Signatures Do Not Match ({similarity:.2f}% similar).")
    except ValueError as e:
        messagebox.showerror("Decryption Error", str(e))
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred: {e}")

# GUI
root = tk.Tk()
root.title("Signature Matching with Encryption")
root.geometry("600x400")

title_label = tk.Label(root, text="Compare Two Signatures", font=("Arial", 14))
title_label.pack(pady=10)

sig1_label = tk.Label(root, text="Signature 1:", font=("Arial", 12))
sig1_label.place(x=20, y=70)

sig1_entry = tk.Entry(root, width=40, font=("Arial", 10))
sig1_entry.place(x=120, y=70)

sig1_capture_button = tk.Button(root, text="Capture", command=lambda: capture_image(sig1_entry, 1))
sig1_capture_button.place(x=500, y=65)

sig1_browse_button = tk.Button(root, text="Browse", command=lambda: browsefunc(sig1_entry))
sig1_browse_button.place(x=400, y=65)

sig2_label = tk.Label(root, text="Signature 2:", font=("Arial", 12))
sig2_label.place(x=20, y=120)

sig2_entry = tk.Entry(root, width=40, font=("Arial", 10))
sig2_entry.place(x=120, y=120)

sig2_capture_button = tk.Button(root, text="Capture", command=lambda: capture_image(sig2_entry, 2))
sig2_capture_button.place(x=500, y=115)

sig2_browse_button = tk.Button(root, text="Browse", command=lambda: browsefunc(sig2_entry))
sig2_browse_button.place(x=400, y=115)

compare_button = tk.Button(root, text="Compare", font=("Arial", 12), command=lambda: check_similarity(root, sig1_entry.get(), sig2_entry.get()))
compare_button.place(x=250, y=200)

root.mainloop()
