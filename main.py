"""
main.py — Live Multi-Camera Layout Simulator

Use your single webcam (or synthetic test feeds) to preview how 1, 2, 3, 4, 5, or 6
cameras look on screen with the responsive grid layout, HUD badges, and flash effects.

Controls:
  [1] - [6] : Switch number of simulated cameras (1 to 6)
  [SPACE]   : Test capture flash effect
  [ESC]     : Exit simulator
"""

import cv2
import numpy as np
import time
import capture

def create_synthetic_frame(cam_id, width=1280, height=720, tick=0):
    """Generate a clean synthetic camera frame with animation if no webcam is open."""
    img = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Subtle color background variation per camera
    colors = [
        (35, 30, 25),
        (25, 35, 30),
        (30, 25, 35),
        (35, 35, 25),
        (25, 30, 35),
        (35, 25, 30),
    ]
    bg_color = colors[cam_id % len(colors)]
    img[:] = bg_color
    
    # Grid lines
    for x in range(0, width, 80):
        cv2.line(img, (x, 0), (x, height), (45, 45, 45), 1)
    for y in range(0, height, 80):
        cv2.line(img, (0, y), (width, y), (45, 45, 45), 1)
        
    # Moving indicator
    cx = int((width // 2) + 150 * np.sin(tick * 0.05 + cam_id))
    cy = int((height // 2) + 80 * np.cos(tick * 0.05 + cam_id))
    cv2.circle(img, (cx, cy), 30, (0, 200, 255), 2)
    cv2.putText(img, f"SIMULATED FEED {cam_id}", (width // 2 - 140, height // 2),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2, cv2.LINE_AA)
    
    return img

def run_simulation():
    print("=" * 55)
    print("   MULTI-CAMERA LAYOUT SIMULATOR")
    print("=" * 55)
    print("Keys:")
    print("  [1] - [6] : Change number of simulated cameras")
    print("  [SPACE]   : Trigger shutter flash effect")
    print("  [ESC]     : Exit")
    print("=" * 55)

    # Try opening camera 0
    cap = cv2.VideoCapture(0)
    has_webcam = cap.isOpened()
    if has_webcam:
        print(" Connected to physical webcam (Camera 0)")
    else:
        print(" No webcam detected — using animated synthetic test feeds")

    num_simulated_cams = 2  # Start with 2 simulated cameras by default
    tick = 0
    flashing = False
    flash_frames_left = 0
    
    status_msg = f"Simulating {num_simulated_cams} cameras. Press 1-6 to change camera count."
    status_frames = 60

    cv2.namedWindow("Layout Simulator (Press 1-6 to switch)", cv2.WINDOW_NORMAL)

    try:
        while True:
            tick += 1
            raw_frame = None
            
            if has_webcam:
                ret, frame = cap.read()
                if ret:
                    raw_frame = frame
            
            # If no frame from webcam, generate synthetic frame
            if raw_frame is None:
                native_w, native_h = 1280, 720
            else:
                native_h, native_w = raw_frame.shape[:2]

            # Build list of simulated camera frames
            simulated_frames = []
            for cam_id in range(num_simulated_cams):
                if raw_frame is not None:
                    # Use real camera frame
                    f = raw_frame.copy()
                    # Add subtle tint or label per simulated camera
                    if cam_id > 0:
                        # Slight tint for secondary feeds so you can distinguish them
                        overlay = np.zeros_like(f)
                        overlay[:, :] = (20 * cam_id, 10 * cam_id, 0)
                        f = cv2.add(f, overlay)
                else:
                    f = create_synthetic_frame(cam_id, width=native_w, height=native_h, tick=tick)
                simulated_frames.append((cam_id, f))

            # Compute responsive grid dimensions
            grid_rows, grid_cols, cell_w, cell_h = capture.compute_grid_dimensions(
                num_simulated_cams, native_w, native_h, max_total_w=1400, max_total_h=800
            )

            # Process and badge each feed
            resized_cells = []
            for cam_id, f in simulated_frames:
                cell = cv2.resize(f, (cell_w, cell_h))
                
                # If currently flashing (capture trigger)
                if flash_frames_left > 0:
                    overlay = cell.copy()
                    cv2.rectangle(overlay, (0, 0), (cell_w, cell_h), (0, 255, 255), -1)
                    cell = cv2.addWeighted(cell, 0.6, overlay, 0.4, 0)

                # Add CAM badge and sample SN
                capture.draw_hud_badge(cell, f"CAM {cam_id}", (12, 28), font_scale=0.7, font_thick=2)
                capture.draw_hud_badge(cell, f"SN: SAMPLE-00{cam_id + 1} (1/1)",
                                       (12, 58), font_scale=0.6, font_thick=1, text_color=(0, 255, 255))
                resized_cells.append(cell)

            if flash_frames_left > 0:
                flash_frames_left -= 1

            # Combine into responsive grid
            combined = capture.grid_layer_camera(resized_cells, rows=grid_rows, cols=grid_cols)

            if combined is not None:
                banner_y = combined.shape[0] - 15
                if status_frames > 0:
                    capture.draw_hud_badge(
                        combined, status_msg, (15, banner_y),
                        font_scale=0.65, font_thick=2, text_color=(0, 255, 0), bg_color=(0, 0, 0), alpha=0.85
                    )
                    status_frames -= 1

                cv2.imshow("Layout Simulator (Press 1-6 to switch)", combined)

            key = cv2.waitKey(15) & 0xFF
            
            # ESC or window closed
            if key == 27 or cv2.getWindowProperty("Layout Simulator (Press 1-6 to switch)", cv2.WND_PROP_VISIBLE) < 1:
                break
            
            # Key 1 to 6: change simulated camera count
            if ord('1') <= key <= ord('6'):
                num_simulated_cams = key - ord('0')
                status_msg = f"Simulating {num_simulated_cams} camera feed(s) [{grid_rows}x{grid_cols} grid]"
                status_frames = 60
            
            # SPACE: trigger flash capture effect
            elif key == 32:
                flash_frames_left = 6
                status_msg = f"Capture Flash Triggered across all {num_simulated_cams} cameras!"
                status_frames = 45

    finally:
        if has_webcam:
            cap.release()
        cv2.destroyAllWindows()
        print("\nSimulator closed.")

if __name__ == "__main__":
    run_simulation()
