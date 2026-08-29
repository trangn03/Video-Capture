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
            # 1. Force MJPEG compression to prevent USB bandwidth saturation
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
            
            # 2. Request full 4K UHD resolution
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 3840)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 2160)
            
            # Verify actual resolution accepted by hardware
            actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            camera_ids.append(i)
            captures.append(cap)
            print(f"Camera {i} connected at {actual_w}x{actual_h}")
        else:
            cap.release()

    print(f"There are {len(camera_ids)} available camera(s) ready to take picture")
    return camera_ids, captures

"""
    Probe camera indices 0 through max_index-1 and return their status and
    resolution info without holding the capture devices open.

    Returns:
        list[dict]: [{'id': int, 'width': int, 'height': int}, ...]
"""
def probe_cameras(max_index=10):
    detected = []
    camera_api = cv2.CAP_DSHOW if os.name == 'nt' else cv2.CAP_ANY

    for i in range(max_index):
        cap = cv2.VideoCapture(i, camera_api)
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 3840)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 2160)
            actual_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            detected.append({"id": i, "width": actual_w, "height": actual_h})
            cap.release()
    return detected


"""
Display grid layer for the camera 
"""
def grid_layer_camera(frames):
    # If no cameras are connected, do nothing to avoid crashing
    if not frames:
        return None
    # Work on a copy so don't mutate the caller's list when padding
    frames = list(frames)
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
    Draw text with a high-contrast dark outline and anti-aliasing.
"""
def draw_text_with_outline(img, text, pos, font_scale, color, thickness=2, outline_color=(0, 0, 0), outline_extra=4):
    x, y = pos
    # Draw dark outline for contrast against any camera background
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, outline_color, thickness + outline_extra, cv2.LINE_AA)
    # Draw main text
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness, cv2.LINE_AA)

"""
    Display yellow flash across all camera feeds to confirm a shot was taken.
"""
def flash_capture(capture_list, camera_ids, target_w, target_h, camera_names=None):
    scale = max(1.0, target_h / 720.0)
    font_scale_cam = 2.0 * scale
    thickness = max(2, int(3 * scale))
    outline_extra = max(2, int(3 * scale))
    x_pos = int(30 * scale)
    y_cam = int(80 * scale)

    def get_label(cid):
        if camera_names and cid in camera_names and camera_names[cid]:
            return camera_names[cid]
        return f"CAM {cid}"

    for _ in range(8):  
        # Trigger all camera shutters simultaneously
        for cap in capture_list:
            cap.grab()

        # Decode the captured frames sequentially, keeping each frame paired
        # with its camera id so labels stay correct even if a camera drops out
        frames = []
        for i, cap in enumerate(capture_list):
            ret, frame = cap.retrieve()
            if ret:
                frames.append((camera_ids[i], frame))

        if frames:
            resized = []
            for cam_id, f in frames:
                # Force the flash frame to the shared dimensions
                resized_f = cv2.resize(f, (target_w, target_h))

                overlay = resized_f.copy()
                cv2.rectangle(overlay, (0, 0), (target_w, target_h), (0, 255, 255), -1)
                resized_f = cv2.addWeighted(resized_f, 0.6, overlay, 0.4, 0)

                draw_text_with_outline(
                    resized_f, get_label(cam_id), (x_pos, y_cam),
                    font_scale_cam, (0, 255, 255), thickness,
                    outline_extra=outline_extra
                )
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
def start_capture(part_number=None, job_number=None, serial_numbers=None, camera_names=None):

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

    # Helper to resolve custom camera names and clean filename tags
    def get_cam_label(cid):
        if camera_names and cid in camera_names and camera_names[cid]:
            return str(camera_names[cid]).strip()
        return f"CAM {cid}"

    def get_cam_tag(cid):
        label = get_cam_label(cid)
        clean = "".join(c for c in label if c.isalnum() or c in ("-", "_"))
        return clean if clean else f"CAM{cid}"

    total = len(serial_numbers)
    sn_index = 0        # tracks which SN in the queue is currently active
    target_h = None     # shared display height across all camera feeds
    target_w = None     # shared display width across all camera feeds
    prev_cam_count = 0  # used to detect camera connect/disconnect events
    last_capture = None # info needed to undo the most recent capture set
    session_capture_sets = 0  # total capture sets taken this session, across all SNs
    confirm_quit = False # true while waiting on the operator to confirm ESC

    # The "All cameras" window is what's actually on screen during
    # capture, so status messages are also shown there as a temporary banner.
    status_message = ""
    status_frames_left = 0

    def notify (msg, frames=45):
        nonlocal status_message, status_frames_left
        print(msg)
        status_message = msg
        status_frames_left = frames

    print("\n[SPACE] to Capture | [R] to Retake Last | [ESC] to Quit (press twice to confirm)")
    
    cv2.namedWindow("All cameras", cv2.WINDOW_NORMAL)

    try:
        while True:
            # Trigger all camera shutters simultaneously
            for cap in capture_list:
                cap.grab()

            # Decode the captured frames sequentially, keeping each frame paired
            # with its camera id so labels/filenames stay correct even if a
            # camera in the middle of the list fails to retrieve.
            frames = []
            for i, cap in enumerate(capture_list):
                ret, frame = cap.retrieve()
                if not ret:
                    # Quick retry grab in case of USB hub timing glitch
                    cap.grab()
                    ret, frame = cap.retrieve()
                if ret:
                    frames.append((camera_ids[i], frame))
                else:
                    print(f"Warning: Camera {camera_ids[i]} ({get_cam_label(camera_ids[i])}) failed to retrieve frame.")

            # Recalculate display height only when the number of active cameras changes
            if len(frames) != prev_cam_count:
                # Find the smallest height among all cameras to use as the baseline
                target_h = min(f.shape[0] for _, f in frames) if frames else None
                target_w = min(f.shape[1] for _, f in frames) if frames else None
                prev_cam_count = len(frames)
            # Check if we have processed all the typed-in serial numbers
            queue_done = serial_numbers and sn_index >= total

            if frames:
                # Scale overlay fonts and margins proportionally to frame resolution (e.g. 4K, 1080p)
                scale = max(1.0, target_h / 720.0) if target_h else 1.0
                font_scale_cam = 2.0 * scale
                font_scale_sn = 1.6 * scale
                thickness = max(2, int(3 * scale))
                outline_extra = max(2, int(3 * scale))
                x_pos = int(30 * scale)
                y_cam = int(80 * scale)
                y_sn = int(160 * scale)

                # Determine which SN to display on the screen
                current_sn = serial_numbers[sn_index] if serial_numbers and not queue_done else None
                resized = []
                for cam_id, f in frames:
                    resized_f = cv2.resize(f, (target_w, target_h))

                    # Display custom camera label with contrast outline
                    draw_text_with_outline(
                        resized_f, get_cam_label(cam_id), (x_pos, y_cam),
                        font_scale_cam, (0, 255, 255), thickness,
                        outline_extra=outline_extra
                    )

                    # Display current SN and queue progress if serial numbers were entered
                    if current_sn:
                        draw_text_with_outline(
                            resized_f, f"SN: {current_sn}  ({sn_index + 1} of {total})",
                            (x_pos, y_sn), font_scale_sn, (0, 255, 255), thickness,
                            outline_extra=outline_extra
                        )
                    elif queue_done:
                        draw_text_with_outline(
                            resized_f, "All SNs captured - [R] Retake  [ESC] Finish",
                            (x_pos, y_sn), font_scale_sn * 0.85, (0, 255, 255), thickness,
                            outline_extra=outline_extra
                        )
                    resized.append(resized_f)

                # Stack all camera feeds into grid layer
                combined = grid_layer_camera(resized)
                if combined is not None:
                    banner_scale = max(1.0, target_h / 720.0) if target_h else 1.0
                    banner_font_scale = 1.6 * banner_scale
                    banner_thickness = max(2, int(3 * banner_scale))
                    banner_outline = max(2, int(3 * banner_scale))
                    banner_x = int(35 * banner_scale)
                    banner_y = combined.shape[0] - int(50 * banner_scale)

                    if confirm_quit:
                        # Persistent prompt overrides the normal status banner
                        # until the operator confirms or cancels the quit.
                        draw_text_with_outline(
                            combined,
                            "Quit session? Press ESC again to confirm, or any other key to keep capturing.",
                            (banner_x, banner_y), banner_font_scale * 0.9, (0, 0, 255),
                            banner_thickness, outline_extra=banner_outline
                        )
                    elif status_frames_left > 0:
                        # Draw the latest status message as a temporary banner across
                        # the bottom of the window (the only visible surface in the GUI build)
                        draw_text_with_outline(
                            combined, status_message,
                            (banner_x, banner_y), banner_font_scale, (0, 255, 0),
                            banner_thickness, outline_extra=banner_outline
                        )
                        status_frames_left -= 1
                    cv2.imshow("All cameras", combined)

            key = cv2.waitKey(1) & 0xFF

            # Detect the window being closed via the title bar's X button
            if frames and cv2.getWindowProperty("All cameras", cv2.WND_PROP_VISIBLE) < 1:
                break

            if confirm_quit:
                # Any real keypress resolves the prompt: ESC confirms, anything
                # else cancels and resumes the session without side effects.
                if key == 27:
                    break
                elif key != 255:
                    confirm_quit = False
                    notify("Quit cancelled. Continuing capture.")
                continue

            if key == 27:  # ESC — ask for confirmation before quitting
                confirm_quit = True
            elif key == 32 and queue_done:  # SPACE — no SN left to capture for
                notify("All serial numbers captured. Press R to retake the last set or ESC to finish.")
            elif key == 32:  # SPACE — save current frames
                current_sn = serial_numbers[sn_index] if serial_numbers else None
                sn_folder = target_folder_for(current_sn)
                count_img = next_count(sn_folder)
                saved_files = []
                write_failed = False
                for cam_id, frame in frames:
                    cam_tag = get_cam_tag(cam_id)
                    # Include SN in filename too, for extra safety if files get moved around
                    if current_sn:
                        filename = os.path.join(
                            sn_folder, f"PART_{part_number}_{cam_tag}_SN{current_sn}_{count_img}.jpg")
                    else:
                        filename = os.path.join(
                            sn_folder, f"PART_{part_number}_{cam_tag}_{count_img}.jpg")
                    if cv2.imwrite(filename, frame):
                        saved_files.append(filename)
                    else:
                        write_failed = True
                        print(f"Error: failed to save {filename}")

                # Trigger the flashing effect confirmation
                if target_h:
                    flash_capture(capture_list, camera_ids, target_w, target_h, camera_names=camera_names)

                if write_failed:
                    notify(f"WARNING: some images failed to save for set {count_img}")
                else:
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

        # Open the output folder in File Explorer so the operator can verify
        # the images right away, without hunting for the path themselves.
        if total_captures > 0 and os.name == 'nt':
            os.startfile(os.path.abspath(folder))


if __name__ == "__main__":
    try:
        start_capture()
    except Exception as e:
        print(f"\n CRASHED: {e}")
    input("\nPress ENTER to close the window.")