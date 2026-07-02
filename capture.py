import os
os.environ["OPENCV_LOG_LEVEL"] = "SILENT"  # suppress OpenCV console noise
import cv2
import re
import numpy as np

"""
    Scan the output folder for existing captured images and return the next
    available set number so captures resume without overwriting prior images.

    Returns 1 if the folder is empty or has no matching files.
"""
def find_existing_img(folder):
    files = os.listdir(folder)
    numbers = []
    for f in files:
        # Match filenames ending in _<number>.jpg (the set counter)
        match = re.search(r'_(\d+)\.jpg$', f)
        if match:
            numbers.append(int(match.group(1)))
    return max(numbers) + 1 if numbers else 1

"""
    Probe camera indices 0 through max_index-1 and return only the ones
    that successfully open.

    Returns:
        camera_ids (list[int]): indices of connected cameras
        captures   (list[cv2.VideoCapture]): already-open capture objects
"""
def find_all_cameras(max_index=10):

    camera_ids = []
    captures = []
    for i in range(max_index):
        cap = cv2.VideoCapture(i, cv2.CAP_ANY)
        if cap.isOpened():
            camera_ids.append(i)
            captures.append(cap)  # keep open for the session
            print(f"Camera {i} ... connected.")
        else:
            cap.release()

    print(f"There are {len(camera_ids)} available camera(s) ready to take picture")
    return camera_ids, captures

"""
    Display yellow flash across all camera feeds to confirm a shot was taken.
"""
def flash_capture(capture_list, camera_ids, target_h):

    for _ in range(8):  # 8 frames * 30ms = ~240ms flash duration
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
                # Solid yellow rectangle over the frame 
                overlay = resized_f.copy()
                cv2.rectangle(overlay, (0, 0), (new_w, target_h), (0, 255, 255), -1)
                resized_f = cv2.addWeighted(resized_f, 0.6, overlay, 0.4, 0)
                cv2.putText(resized_f, f"CAM {camera_ids[i]}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                resized.append(resized_f)
            combined = np.hstack(resized)
            cv2.imshow("All cameras", combined)
            cv2.waitKey(30)

"""
    Main capture session:
      1. Detect all connected cameras.
      2. Prompt for part number and job number (used for folder structure).
      3. Optionally collect a batch of serial numbers upfront.
      4. Open the live camera feed and wait for SPACE to capture or ESC to quit.
      5. Each SPACE press saves one image per camera and advances to the next SN.
"""
def start_capture():

    print("Capture begin...This may take a moment")

    camera_ids, capture_list = find_all_cameras(10)
    if not camera_ids:
        print("Error: Couldn't detect any camera. Please check the connection and try again.")
        return

    # Input part number and job number for file path
    part_number = input("Enter PART NUMBER: ").strip() or "UNKNOWN"
    job_number = input("Enter JOB NUMBER: ").strip() or "TEMP"

    # Images are saved under: <PART_NUMBER>/JOB_<JOB_NUMBER>/
    folder = os.path.join(f"{part_number}", f"JOB_{job_number}")
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"Created folder: {folder}")

    print(f"\n Saving to: {os.path.abspath(folder)}")

    # If images already exist in the folder, pick up numbering where it left off
    count_img = find_existing_img(folder)
    if count_img > 1:
        print(f"Existing photo found. Resuming at img #{count_img}")

    # Collect all serial numbers before opening the camera so the operator
    # isn't interrupted mid-session by terminal prompts
    print("\nEnter serial numbers one per line. Use ENTER again when done: ")
    serial_numbers = []
    while True:
        sn = input(f"  SN {len(serial_numbers) + 1}: ").strip()
        if not sn:
            break
        serial_numbers.append(sn)

    if serial_numbers:
        print(f"{len(serial_numbers)} serial number(s) queued.")
    else:
        print("No serial numbers entered. Captures will start and save without SN.")

    total = len(serial_numbers)
    sn_index = 0       # tracks which SN in the queue is currently active
    target_h = None    # shared display height across all camera feeds
    prev_cam_count = 0 # used to detect camera connect/disconnect events

    print("\n[SPACE] to Capture | [ESC] to Quit")

    try:
        while True:
            # Read one frame from each camera
            frames = []
            for i, cap in enumerate(capture_list):
                ret, frame = cap.read()
                if ret:
                    frames.append(frame)
                else:
                    print(f"Warning: Camera {camera_ids[i]} failed to read frame.")

            # Recalculate display height only when the number of active cameras changes
            if len(frames) != prev_cam_count:
                target_h = min(f.shape[0] for f in frames) if frames else None
                prev_cam_count = len(frames)

            if frames:
                current_sn = serial_numbers[sn_index] if serial_numbers else None
                resized = []
                for i, f in enumerate(frames):
                    # Scale each frame to the shared target height, preserving aspect ratio
                    h, w = f.shape[:2]
                    new_w = int(w * target_h / h)
                    resized_f = cv2.resize(f, (new_w, target_h))

                    # Display camera label
                    cv2.putText(resized_f, f"CAM {camera_ids[i]}", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

                    # Display current SN and queue progress if serial numbers were entered
                    if current_sn:
                        cv2.putText(resized_f, f"SN: {current_sn}  ({sn_index + 1} of {total})",
                                    (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                    resized.append(resized_f)

                # Stack all camera feeds side by side into one window
                combined = np.hstack(resized)
                cv2.imshow("All cameras", combined)

            key = cv2.waitKey(1) & 0xFF

            if key == 27:  # ESC — exit session
                break
            elif key == 32:  # SPACE — save current frames
                current_sn = serial_numbers[sn_index] if serial_numbers else None
                for i, frame in enumerate(frames):
                    cam_id = camera_ids[i]
                    # Include SN in filename only when one is active
                    if current_sn:
                        filename = f"{folder}/PART_{part_number}_CAM{cam_id}_SN{current_sn}_{count_img}.jpg"
                    else:
                        filename = f"{folder}/PART_{part_number}_CAM{cam_id}_{count_img}.jpg"
                    cv2.imwrite(filename, frame)

                if target_h:
                    flash_capture(capture_list, camera_ids, target_h)

                sn_info = f" | SN: {current_sn}" if current_sn else ""
                print(f"--- Capture set {count_img}{sn_info} complete ---")
                count_img += 1

                # Go to the next SN; stop automatically when the queue is empty
                if serial_numbers:
                    sn_index += 1
                    if sn_index >= total:
                        print("\nAll serial numbers captured.")
                        break

    finally:
        # Release cameras and close windows, even if the session crashed
        for cap in capture_list:
            cap.release()
        cv2.destroyAllWindows()
        print(f"\nAll images are stored in: {os.path.abspath(folder)}")


if __name__ == "__main__":
    try:
        start_capture()
    except Exception as e:
        print(f"\n CRASHED: {e}")
        input("\nPress ENTER to close the window.")
