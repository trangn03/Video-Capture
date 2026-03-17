import os
import cv2
import datetime

def start_capture():
    # Get user input
    part_number = input("Enter part number:").strip()
    job_number = input("Enter job number:").strip()
    
    # create folder
    folder = f"JOB_{job_number}_PART_{part_number}"
    if not os.path.exists(folder):
        os.makedirs(folder)
        
    capture = cv2.VideoCapture(0)
    
    import time
    time.sleep(1)
    
    if not capture.isOpened():
        print("Error: Could not access the camera. Please check the permission and try again")
        
    print(f"\n Saving to: {os.path.abspath(folder)}")
    print("📸 [SPACE] to Capture | [ESC] to Quit")
    
    count = 1
    while True:
        ret, frame = capture.read()
        if not ret:
            break
        
        cv2.imshow("Preview",frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == 27: # esc
            break
        elif key == 32: # space
            filename = f"{folder}/PART_{part_number}_{count}.jpg"
            
            cv2.imwrite(filename, frame)
            print(f"Captured: {filename}")
            count +=1
            
    capture.release()
    cv2.destroyAllWindows()
    
if __name__ == "__main__":
    start_capture()
    