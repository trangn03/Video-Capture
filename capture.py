import os
os.environ["OPENCV_LOG_LEVEL"] = "SILENT"
import cv2 #capture video
import datetime
import time
import re
import platform
import subprocess
import numpy as np

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
    Return:
        camera_id = list of valid camera
        captures: list of already-open VideoCapture object
    Set maximum camera to check to 5 (0-4) temporarily, can be adjusted later if needed
"""
def find_all_cameras(camera=10):
    camera_ids = []
    captures = []
    for i in range(camera):
        cap = cv2.VideoCapture(i, cv2.CAP_ANY) #CAP_DSHOW
        if cap.isOpened():
            camera_ids.append(i)
            captures.append(cap) #keep open
            print(f"Camera {i} ... connected.")
        else:
            cap.release()
    
    print(f"There are {len(camera_ids)} available camera(s) ready to take picture")
    
    return camera_ids, captures

def flash_green(capture_list, camera_ids, target_h):
    for _ in range(8):
        frames = []
        for cap in capture_list:
            ret, frame = cap.read()
            if ret:
                frames.append(frame)
        if frames:
            resized = []
            for i, f in enumerate(frames):
                h, w = f.shape[:2]
                new_w = int(w * target_h / h)
                resized_f = cv2.resize(f, (new_w, target_h))
                overlay = resized_f.copy()
                cv2.rectangle(overlay, (0, 0), (new_w, target_h), (0, 255, 255), -1)
                resized_f = cv2.addWeighted(resized_f, 0.6, overlay, 0.4, 0)
                cv2.putText(resized_f, f"CAM {camera_ids[i]}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                resized.append(resized_f)
            combined = np.hstack(resized)
            cv2.imshow("All cameras", combined)
            cv2.waitKey(30)

def start_capture():
    print("Capture begin...")
    # Find all cameras
    camera_ids, capture_list = find_all_cameras(10)
    if not camera_ids:
        print("Error: Couldn't detect any camera. Please check the connection and try again.")
        return

    # Get user input
    part_number = input("Enter PART NUMBER: ").strip() or "UNKNOWN"
    job_number = input("Enter JOB NUMBER: ").strip() or "TEMP"

    # create folder
    folder = os.path.join(f"{part_number}", f"JOB_{job_number}")
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"Created folder: {folder}")


    print(f"\n Saving to: {os.path.abspath(folder)}")
    print("[SPACE] to Capture | [ESC] to Quit")


    # resume numbering if images already exist in the folder
    # create counter for image
    count_img = find_existing_img(folder)
    if count_img > 1:
        print(f"Existing photo found. Resuming at img #{count_img}")

    time.sleep(1)
    target_h = None

    try:
        while True:
            # List to store frames from all cameras
            frames = []
            for cap in capture_list:
                ret, frame = cap.read()
                if ret:
                    frames.append(frame)

            if frames:
                target_h = min(f.shape[0] for f in frames)
                resized = []
                for i, f in enumerate(frames):
                    h, w = f.shape[:2]
                    new_w = int(w * target_h / h)
                    resized_f = cv2.resize(f, (new_w, target_h))
                    cv2.putText(resized_f, f"CAM {camera_ids[i]}", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                    resized.append(resized_f)

                combined = np.hstack(resized)
                cv2.imshow("All cameras", combined)

            key = cv2.waitKey(1) & 0xFF

            # Quit on ESC, Capture on SPACE
            if key == 27: # esc
                break
            elif key == 32: # space
                # Iterate through the frames
                for i, frame in enumerate(frames):
                    if frame is not None:
                        cam_id = camera_ids[i]
                        filename = f"{folder}/PART_{part_number}_CAM{cam_id}_{count_img}.jpg"
                        cv2.imwrite(filename, frame)

                if target_h:
                    flash_green(capture_list, camera_ids, target_h)
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