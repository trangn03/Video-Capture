import os
import cv2 #capture video
import datetime
import time
import re
import platform
import subprocess

"""
    Check the input folder for any existing images
    If there are existing images, find the highest number and start from the next number
"""
def find_existing_img(folder):
    files = os.listdir(folder)
    numbers = []
    for f in files:
        # Matches the pattern "_<number>.jpg" at the end of the filename
        match = re.search(r'_(\d+)\.jpg$', f)
        if match:
            # If found then add the number to the list
            numbers.append(int(match.group(1)))
    # Return the maximum number + 1, or 1 if there are no existing images
    return max(numbers) + 1 if numbers else 1

"""
    Check for how many cameras are plugged in
    Return a list of available camera indices
    Set maximum camera to check to 5 (0-4) temporarily, can be adjusted later if needed
"""
def find_all_cameras(camera=5):
    available = []
    for i in range(camera):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            available.append(i)
            cap.release()
    return available

def start_capture():
    print("Capture begin...")
    # Find all cameras
    camera_count = find_all_cameras(5)
    if not camera_count:
        print("Error: Couldn't detect any camera. Please check the connection and try again.")
        return
    
    print(f"There are {camera_count} available camera ready to take picture")
    
    # Get user input
    part_number = input("Enter PART NUMBER: ").strip() or "UNKNOWN"
    job_number = input("Enter JOB NUMBER: ").strip() or "TEMP"
    
    # create folder
    folder = os.path.join(f"{part_number}", f"JOB_{job_number}")
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"Created folder: {folder}")
    
    # 0 is the default camera     
    # Initialize all cameras and store them in a list
    capture_list = []
    for i in camera_count:
        cap_pic = cv2.VideoCapture(i)
        capture_list.append(cap_pic)

    time.sleep(1)
    
    # if not capture.isOpened():
    #     print("Error: Could not access the camera. Please check the permission and try again.")
        
    print(f"\n Saving to: {os.path.abspath(folder)}")
    print("[SPACE] to Capture | [ESC] to Quit")
    
    # create counter for image
    count_img = find_existing_img(folder)
    if count_img > 1:
        print(f"Existing photo found. Resuming at img #{count_img}")
        
    try: 
        while True:
            # List to store frames from all cameras
            frames = []
            for i, cap in enumerate(capture_list):
                ret, frame = cap.read()
                if ret:
                    frames.append(frame)
                    # Display separate window for each camera feed
                    cv2.imshow(f"Camera {camera_count[i]}", frame)
                else:
                    frames.append(None)
        
            key = cv2.waitKey(1) & 0xFF

            # Quit on ESC, Capture on SPACE
            if key == 27: # esc
                break
            elif key == 32: # space
                # Iterate through the frames 
                for i, frame in enumerate(frames):
                    if frame is not None:
                        cam_id = camera_count[i]
                        filename = f"{folder}/PART_{part_number}_CAM{cam_id}_{count_img}.jpg"
                        cv2.imwrite(filename, frame)

                print(f"--- Capture set {count_img} complete ---\n")
                count_img += 1
            
    finally:
        for cap in capture_list:
            cap.release()
        cv2.destroyAllWindows() # Close all OpenCV windows
        print(f"\nAll images are stored in: {os.path.abspath(folder)}")
    
    
if __name__ == "__main__":
    try:
        start_capture()
    except Exception as e:
        print(f"\n CRASHED: {e}")
        input("\nPress ENTER to close the window.")    