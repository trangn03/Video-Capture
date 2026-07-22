import os
os.environ["OPENCV_LOG_LEVEL"] = "SILENT"  # suppress OpenCV console noise
import cv2
import re
import math
import numpy as np

"""
    Scan the output folder for existing captured images and return the next
    available set number so captures resume without overwriting prior images.

    Returns 1 if the folder is empty or has no matching files.
"""
def find_existing_img(folder):
    # Get a list of all files currently inside the folder 
    files = os.listdir(folder)
    numbers = []
    for f in files:
        # Match filenames ending in _<number>.jpg (the set counter)
        match = re.search(r'_(\d+)\.jpg$', f)
        if match:
            # Convert the extracted string number into an integer and save it to our list
            numbers.append(int(match.group(1)))
    return max(numbers) + 1 if numbers else 1

"""
    Scan the job folder for existing SET_<n> subfolders (used for quantities
    captured without a serial number) and return the next available set number.

    Returns 1 if no SET_ subfolders exist yet.
"""
def find_next_set_number(folder):
    numbers = []
    for name in os.listdir(folder):
        match = re.fullmatch(r'SET_(\d+)', name)
        if match and os.path.isdir(os.path.join(folder, name)):
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
    
    camera_api = cv2.CAP_DSHOW if os.name == 'nt' else cv2.CAP_ANY
    
    for i in range(max_index):
        cap = cv2.VideoCapture(i, camera_api)
        if cap.isOpened():
            # If sucessful, record the ID and keep the stream open
            camera_ids.append(i)
            captures.append(cap)  # keep open for the session
            print(f"Camera {i} ... connected.")
        else:
            # Release the memory if no camera was found at this index
            cap.release()

    print(f"There are {len(camera_ids)} available camera(s) ready to take picture")
    return camera_ids, captures

"""
Display grid layer for the camera 
"""
def grid_layer_camera(frames):
    # If no cameras are connected, do nothing to avoid crashing
    if not frames:
        return None
    # Count how many camera during the capture session
    num_frames = len(frames)
    # Calculate the square dimension
    # ceil() to round up the nearest whole number 
    cols = math.ceil(math.sqrt(num_frames))
    rows = math.ceil(num_frames / cols)
    
    # Looks at the very first camera in the list
    # then takes its dimension (height, width) and generates a brand new image of the exact same size,
    # but filled entirely with zeros. We will have a sized black square
    placeholder_frames = np.zeros_like(frames[0])
    
    # Padding the grid, fewer image > grid slots 
    # adding placeholder to the end of the list 
    while len(frames) < rows * cols:
        frames.append(placeholder_frames)
    
    # Create the grid one row at a time
    grid_rows = [] 
    for r in range(rows):
        # Array Slicing: Grabs a chunk of images from the list.
        # Example for 3 columns: Row 0 grabs indices 0 to 3. Row 1 grabs 3 to 6.
        row_frames = frames[r * cols: (r+1) * cols]
        grid_rows.append(np.hstack(row_frames))
    # Vertical stack - top to bottom
    return np.vstack(grid_rows)

"""
    Display yellow flash across all camera feeds to confirm a shot was taken.
"""
def flash_capture(capture_list, camera_ids, target_w, target_h):
    for _ in range(8):  
        # Trigger all camera shutters simultaneously
        for cap in capture_list:
            cap.grab()

        # Decode the captured frames sequentially
        frames = []
        for i, cap in enumerate(capture_list):
            ret, frame = cap.retrieve()
            if ret:
                frames.append(frame)

        if frames:
            resized = []
            for i, f in enumerate(frames):
                # Force the flash frame to the shared dimensions
                resized_f = cv2.resize(f, (target_w, target_h))
                
                overlay = resized_f.copy()
                cv2.rectangle(overlay, (0, 0), (target_w, target_h), (0, 255, 255), -1)
                resized_f = cv2.addWeighted(resized_f, 0.6, overlay, 0.4, 0)
                
                cv2.putText(resized_f, f"CAM {camera_ids[i]}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)
                resized.append(resized_f)
                
            combined = grid_layer_camera(resized)
            if combined is not None: 
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
def start_capture(part_number=None, job_number=None, serial_numbers=None):

    print("Capture begin...This may take a moment")

    # Initialize the camera
    camera_ids, capture_list = find_all_cameras(10)
    if not camera_ids:
        print("Error: Couldn't detect any camera. Please check the connection and try again.")
        return

    # Input part number and job number for file path if not supplied by caller (e.g. the GUI)
    if part_number is None:
        part_number = input("Enter PART NUMBER: ").strip() or "UNKNOWN"
    if job_number is None:
        job_number = input("Enter JOB NUMBER: ").strip() or "TEMP"

    # Images are saved under: <PART_NUMBER>/JOB_<JOB_NUMBER>/SN_<serial>/
    # so that all images for one serial number live together and can be
    # found without scanning the whole job folder.
    folder = os.path.join(f"{part_number}", f"JOB_{job_number}")
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"Created folder: {folder}")

    print(f"\n Saving to: {os.path.abspath(folder)}")

    # Per-folder image counters, keyed by the folder they're saved into.
    # Populated lazily the first time each SN (or SET_<n>) folder is used,
    # so numbering resumes correctly if that folder already has images.
    img_counts = {}

    # When no serial numbers were entered, each quantity gets its own
    # SET_<n> folder instead of everything dumping into the job folder.
    # next_set is None until the first no-SN capture, then tracks which
    # SET_<n> folder the *next* capture should use.
    qty_state = {"next_set": None}

    def target_folder_for(sn):
        if sn:
            return os.path.join(folder, f"SN_{sn}")
        if not serial_numbers:
            if qty_state["next_set"] is None:
                qty_state["next_set"] = find_next_set_number(folder)
            return os.path.join(folder, f"SET_{qty_state['next_set']}")
        return folder

    def next_count(target_folder):
        if target_folder not in img_counts:
            if not os.path.exists(target_folder):
                os.makedirs(target_folder)
            img_counts[target_folder] = find_existing_img(target_folder)
            if img_counts[target_folder] > 1:
                print(f"Existing photos found in {target_folder}. Resuming at img #{img_counts[target_folder]}")
        return img_counts[target_folder]

    # Collect all serial numbers before opening the camera so the operator
    # isn't interrupted mid-session by terminal prompts
    if serial_numbers is None:
        print("\nEnter serial numbers one per line. Use ENTER again when done: ")
        serial_numbers = []
        seen_sns = set() # A Set function is used to check for duplicate inputs
        while True:
            sn = input(f"  SN {len(serial_numbers) + 1}: ").strip()
            if not sn:
                break # Exit loop if the user hit ENTER
            if sn in seen_sns:
                print(f"  ! '{sn}' already in the list — please enter again.")
                continue
            serial_numbers.append(sn)
            seen_sns.add(sn)
    else:
        # Caller (e.g. the GUI) already collected these — just dedupe while preserving order
        seen_sns = set()
        deduped = []
        for sn in serial_numbers:
            if sn not in seen_sns:
                deduped.append(sn)
                seen_sns.add(sn)
        serial_numbers = deduped

    if serial_numbers:
        print(f"{len(serial_numbers)} serial number(s) queued.")
    else:
        print("No serial numbers entered. Captures will start and save without SN.")

    total = len(serial_numbers)
    sn_index = 0        # tracks which SN in the queue is currently active
    target_h = None     # shared display height across all camera feeds
    target_w = None     # shared display width across all camera feeds
    prev_cam_count = 0  # used to detect camera connect/disconnect events
    last_capture = None # info needed to undo the most recent capture set
    session_capture_sets = 0  # total capture sets taken this session, across all SNs

    # The "All cameras" window is what's actually on screen during
    # capture, so status messages are also shown there as a temporary banner.
    status_message = ""
    status_frames_left = 0

    def notify (msg, frames=45):
        nonlocal status_message, status_frames_left
        print(msg)
        status_message = msg
        status_frames_left = frames

    print("\n[SPACE] to Capture | [R] to Retake Last | [ESC] to Quit")
    
    cv2.namedWindow("All cameras", cv2.WINDOW_NORMAL)

    try:
        while True:
            # Trigger all camera shutters simultaneously
            for cap in capture_list:
                cap.grab()

            # Decode the captured frames sequentially
            frames = []
            for i, cap in enumerate(capture_list):
                ret, frame = cap.retrieve()
                if ret:
                    frames.append(frame)
                else:
                    print(f"Warning: Camera {camera_ids[i]} failed to retrieve frame.")
            
            # Recalculate display height only when the number of active cameras changes
            if len(frames) != prev_cam_count:
                # Find the smallest height among all cameras to use as the baseline
                target_h = min(f.shape[0] for f in frames) if frames else None
                target_w = min(f.shape[1] for f in frames) if frames else None
                prev_cam_count = len(frames)
            # Check if we have processed all the typed-in serial numbers
            queue_done = serial_numbers and sn_index >= total

            if frames:
                # Determine which SN to display on the screen
                current_sn = serial_numbers[sn_index] if serial_numbers and not queue_done else None
                resized = []
                for i, f in enumerate(frames):
                    # Scale each frame to the shared target height, preserving aspect ratio
                    # h, w = f.shape[:2]
                    # new_w = int(w * target_h / h)
                    resized_f = cv2.resize(f, (target_w, target_h))

                    # Display camera label
                    cv2.putText(resized_f, f"CAM {camera_ids[i]}", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

                    # Display current SN and queue progress if serial numbers were entered
                    if current_sn:
                        cv2.putText(resized_f, f"SN: {current_sn}  ({sn_index + 1} of {total})",
                                    (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                    elif queue_done:
                        cv2.putText(resized_f, "All SNs captured - [R] Retake  [ESC] Finish",
                                    (10, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                    resized.append(resized_f)

                # Stack all camera feeds into grid layer
                combined = grid_layer_camera(resized)
                if combined is not None:
                    # Draw the latest status message as a temporary banner across
                    # the bottom of the window (the only visible surface in the GUI build)
                    if status_frames_left > 0:
                        banner_y = combined.shape[0] - 20
                        cv2.putText(combined, status_message, (10, banner_y),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        status_frames_left -= 1
                    cv2.imshow("All cameras", combined)

            key = cv2.waitKey(1) & 0xFF

            # Detect the window being closed via the title bar's X button
            if frames and cv2.getWindowProperty("All cameras", cv2.WND_PROP_VISIBLE) < 1:
                break

            if key == 27:  # ESC — exit session
                break
            elif key == 32 and queue_done:  # SPACE — no SN left to capture for
                notify("All serial numbers captured. Press R to retake the last set or ESC to finish.")
            elif key == 32:  # SPACE — save current frames
                current_sn = serial_numbers[sn_index] if serial_numbers else None
                sn_folder = target_folder_for(current_sn)
                count_img = next_count(sn_folder)
                saved_files = []
                for i, frame in enumerate(frames):
                    cam_id = camera_ids[i]
                    # Include SN in filename too, for extra safety if files get moved around
                    if current_sn:
                        filename = f"{sn_folder}/PART_{part_number}_CAM{cam_id}_SN{current_sn}_{count_img}.jpg"
                    else:
                        filename = f"{sn_folder}/PART_{part_number}_CAM{cam_id}_{count_img}.jpg"
                    cv2.imwrite(filename, frame)
                    saved_files.append(filename)

                # Trigger the flashing effect confirmation
                if target_h:
                    flash_capture(capture_list, camera_ids, target_w, target_h)

                sn_info = f" | SN: {current_sn}" if current_sn else ""
                notify(f"Capture set {count_img}{sn_info} complete")

                # Remember this capture so it can be undone with [R]
                used_set_number = qty_state["next_set"] if not current_sn and not serial_numbers else None
                last_capture = {
                    "files": saved_files, "folder": sn_folder, "count_img": count_img,
                    "sn_index": sn_index, "set_number": used_set_number,
                }
                img_counts[sn_folder] = count_img + 1
                if used_set_number is not None:
                    qty_state["next_set"] += 1
                session_capture_sets += 1

                # Go to the next SN; wait for ESC (or R to retake) once the queue is empty
                if serial_numbers:
                    sn_index += 1
                    if sn_index >= total:
                        notify("All serial numbers captured. Press R to retake the last set or ESC to finish.")
            elif key in (ord('r'), ord('R')):  # R — retake the last capture set
                if last_capture is None:
                    notify("Nothing to retake.")
                else:
                    # Delete the previous images from the hard drive
                    for f in last_capture["files"]:
                        if os.path.exists(f):
                            os.remove(f)
                    # Roll back the variables to match the state before the capture was taken
                    img_counts[last_capture["folder"]] = last_capture["count_img"]
                    if last_capture["set_number"] is not None:
                        qty_state["next_set"] = last_capture["set_number"]
                    if serial_numbers:
                        sn_index = last_capture["sn_index"]
                    notify(f"Capture set {last_capture['count_img']} discarded. Ready to retake.")
                    session_capture_sets -= 1
                    # Clear the history so there is no double-undo
                    last_capture = None

    finally:
        # Release cameras and close windows, even if the session crashed
        for cap in capture_list:
            cap.release()
        cv2.destroyAllWindows()

        # Session summary
        total_captures = session_capture_sets
        total_images = total_captures * len(camera_ids)
        print("\n" + "=" * 40)
        print("         SESSION SUMMARY")
        print("=" * 40)
        print(f"  Part Number : {part_number}")
        print(f"  Job Number  : {job_number}")
        print(f"  Capture Sets: {total_captures}")
        print(f"  Images Saved: {total_images}")
        if serial_numbers:
            captured_sns = serial_numbers[:sn_index]
            missed_sns = serial_numbers[sn_index:]
            if captured_sns:
                print(f"  SNs Captured: {', '.join(captured_sns)}")
            if missed_sns:
                print(f"  SNs Missed  : {', '.join(missed_sns)}")
        print(f"  Saved To    : {os.path.abspath(folder)}")
        print("=" * 40 + "\n")


if __name__ == "__main__":
    try:
        start_capture()
    except Exception as e:
        print(f"\n CRASHED: {e}")
    input("\nPress ENTER to close the window.")
