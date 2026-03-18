import os
import cv2 #capture video
import datetime
import time
import re
import platform
import subprocess

def find_existing_img(folder):
    files = os.listdir(folder)
    numbers = []
    for f in files:
        match = re.search(r'_(\d+)\.jpg$', f)
        if match:
            numbers.append(int(match.group(1)))
    return max(numbers) + 1 if numbers else 1

def start_capture():
    print("Capture begin...")
    # Get user input
    part_number = input("Enter PART NUMBER: ").strip() or "UNKNOWN"
    job_number = input("Enter JOB NUMBER: ").strip() or "TEMP"
    
    # create folder
    folder = os.path.join(f"{part_number}", f"JOB_{job_number}")
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"Created folder: {folder}")
    
    # 0 is the default camera     
    capture = cv2.VideoCapture(0)

    time.sleep(1)
    
    if not capture.isOpened():
        print("Error: Could not access the camera. Please check the permission and try again.")
        
    print(f"\n Saving to: {os.path.abspath(folder)}")
    print("[SPACE] to Capture | [ESC] to Quit")
    
    # create counter for image
    count_img = find_existing_img(folder)
    if count_img > 1:
        print(f"Existing photo found. Resuming at img #{count_img}")
    while True:
        ret, frame = capture.read()
        if not ret:
            break
        
        cv2.imshow("Preview Pane",frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == 27: # esc
            break
        elif key == 32: # space
            filename = f"{folder}/PART_{part_number}_{count_img}.jpg"
            
            cv2.imwrite(filename, frame)
            print(f"Captured: {filename}")
            count_img +=1
            
    capture.release()
    cv2.destroyAllWindows()
    print(f"\n All images are stored in: {os.path.abspath(folder)}")
    
    
if __name__ == "__main__":
    try:
        start_capture()
    except Exception as e:
        print("f\n CRASHED: {e}")
        input("\nPress ENTER to close the window.")    