"""
main.py — Multi-Camera Live Layout with Connection Status Indicators

Demonstrates:
  1. Live Camera Connection Status Indicators (🟢 LIVE / 🔴 DISCONNECTED).
  2. Per-camera resolution and live FPS badges.
  3. Disconnect simulation & auto-detection (Press [D] to simulate camera drop/reconnect).
  4. Clean responsive grid layout with shutter flash.

Controls:
  [1] - [6] : Change number of connected cameras (1 to 6)
  [D]       : Toggle Camera 1 Disconnected / Reconnected (test status warning)
  [SPACE]   : Trigger capture flash effect
  [ESC]     : Exit simulator
"""

import cv2
import numpy as np
import math
import time

# ---- Color Palette (BGR format for OpenCV) -----------------------------------
COLOR_LIVE       = (80, 220, 100)     # Emerald Green (Connected / Streaming)
COLOR_DISCONN    = (60, 60, 230)      # Bright Red (Disconnected / Signal Lost)
COLOR_WARNING    = (0, 200, 255)      # Amber / Yellow (Reconnecting / Dropped frame)
BG_DARK          = (20, 20, 26)       # Dark slate canvas


def create_synthetic_frame(cam_id, width=1280, height=720, tick=0):
    """Generate a clean synthetic camera frame."""
    img = np.zeros((height, width, 3), dtype=np.uint8)
    colors = [
        (35, 30, 25), (25, 35, 30), (30, 25, 35),
        (35, 35, 25), (25, 30, 35), (35, 25, 30),
    ]
    bg_color = colors[cam_id % len(colors)]
    img[:] = bg_color

    for x in range(0, width, 80):
        cv2.line(img, (x, 0), (x, height), (45, 45, 45), 1)
    for y in range(0, height, 80):
        cv2.line(img, (0, y), (width, y), (45, 45, 45), 1)

    cx = int((width // 2) + 140 * np.sin(tick * 0.05 + cam_id))
    cy = int((height // 2) + 80 * np.cos(tick * 0.05 + cam_id))
    cv2.circle(img, (cx, cy), 32, (0, 200, 255), 2)
    cv2.circle(img, (cx, cy), 5, (0, 255, 0), -1)

    cv2.putText(img, f"CAMERA {cam_id} FEED", (width // 2 - 130, height // 2),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2, cv2.LINE_AA)
    return img


def create_disconnected_slot(cam_id, width, height):
    """Render a clean alert tile when a camera is disconnected."""
    img = np.zeros((height, width, 3), dtype=np.uint8)
    img[:] = (25, 20, 30)

    # Diagonal warning hatch lines
    for x in range(-height, width + height, 40):
        cv2.line(img, (x, 0), (x + height, height), (35, 28, 42), 2)

    # Red warning box in center
    cx, cy = width // 2, height // 2
    cv2.circle(img, (cx, cy - 30), 28, COLOR_DISCONN, 3)
    cv2.line(img, (cx, cy - 42), (cx, cy - 25), COLOR_DISCONN, 3)
    cv2.circle(img, (cx, cy - 15), 3, COLOR_DISCONN, -1)

    cv2.putText(img, f"CAMERA {cam_id} DISCONNECTED", (cx - 150, cy + 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (230, 230, 240), 2, cv2.LINE_AA)
    cv2.putText(img, "Check USB cable / connection", (cx - 135, cy + 58),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (140, 140, 160), 1, cv2.LINE_AA)
    return img


def draw_status_badge(img, cam_id, is_connected, resolution_text="3840x2160", fps=30):
    """Draw a connection status pill in the top-left of the camera feed."""
    h, w = img.shape[:2]
    scale = max(0.85, h / 720.0)

    # Badge background
    badge_w = int(240 * scale)
    badge_h = int(58 * scale)
    x1, y1 = 14, 14
    x2, y2 = x1 + badge_w, y1 + badge_h

    # Semi-transparent dark background for contrast
    sub = img[y1:y2, x1:x2]
    rect = np.zeros_like(sub)
    rect[:] = (15, 15, 20)
    cv2.addWeighted(sub, 0.25, rect, 0.75, 0, sub)
    cv2.rectangle(img, (x1, y1), (x2, y2), (60, 60, 80), 1)

    # Status LED Dot & Text
    dot_x = x1 + int(14 * scale)
    dot_y = y1 + int(20 * scale)
    dot_radius = int(6 * scale)

    if is_connected:
        # Glowing Green LED
        cv2.circle(img, (dot_x, dot_y), dot_radius + 2, (40, 140, 60), 1)
        cv2.circle(img, (dot_x, dot_y), dot_radius, COLOR_LIVE, -1)

        # Labels
        cv2.putText(img, f"CAM {cam_id}  [LIVE]", (dot_x + int(12 * scale), dot_y + int(5 * scale)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55 * scale, (240, 240, 250), 2, cv2.LINE_AA)
        cv2.putText(img, f"{resolution_text} | {fps} FPS", (x1 + int(14 * scale), y1 + int(44 * scale)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42 * scale, (160, 160, 180), 1, cv2.LINE_AA)
    else:
        # Red Blinking / Solid LED
        cv2.circle(img, (dot_x, dot_y), dot_radius + 2, (30, 30, 120), 1)
        cv2.circle(img, (dot_x, dot_y), dot_radius, COLOR_DISCONN, -1)

        # Disconnected label
        cv2.putText(img, f"CAM {cam_id}  [OFFLINE]", (dot_x + int(12 * scale), dot_y + int(5 * scale)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55 * scale, COLOR_DISCONN, 2, cv2.LINE_AA)
        cv2.putText(img, "SIGNAL LOST", (x1 + int(14 * scale), y1 + int(44 * scale)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42 * scale, COLOR_DISCONN, 1, cv2.LINE_AA)


def build_camera_grid(cells, max_w=1280, max_h=720):
    """Stack camera cells into a clean responsive grid."""
    n = len(cells)
    if n == 0:
        return np.zeros((max_h, max_w, 3), dtype=np.uint8)

    cols = math.ceil(math.sqrt(n))
    rows = math.ceil(n / cols)

    cell_w = max_w // cols
    cell_h = max_h // rows

    resized = [cv2.resize(c, (cell_w, cell_h)) for c in cells]
    blank = np.zeros((cell_h, cell_w, 3), dtype=np.uint8)
    while len(resized) < rows * cols:
        resized.append(blank)

    grid_rows = []
    for r in range(rows):
        grid_rows.append(np.hstack(resized[r * cols: (r + 1) * cols]))

    return np.vstack(grid_rows)


def run_simulation():
    print("=" * 60)
    print("   CAMERA CONNECTION STATUS INDICATOR SIMULATOR")
    print("=" * 60)
    print("Keys:")
    print("  [1] - [6] : Change number of connected cameras")
    print("  [D]       : Simulate Disconnect / Reconnect on Camera 1")
    print("  [SPACE]   : Trigger capture flash effect")
    print("  [ESC]     : Exit")
    print("=" * 60)

    # Check for real webcam
    cap = cv2.VideoCapture(0)
    has_webcam = cap.isOpened()
    if has_webcam:
        print(" Connected to physical webcam (Camera 0)")
    else:
        print(" No physical webcam — using synthetic camera feeds")

    num_cameras = 2
    cam1_simulated_disconnect = False
    tick = 0
    flash_frames = 0
    last_time = time.time()
    fps_display = 30

    window_name = "Multi-Camera View with Connection Status"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    try:
        while True:
            tick += 1
            now = time.time()
            dt = now - last_time
            if dt > 0.5:
                fps_display = int(1.0 / max(0.001, (dt / 15)))
                last_time = now

            # 1. Grab frame if physical webcam available
            raw_frame = None
            if has_webcam:
                ret, frame = cap.read()
                if ret:
                    raw_frame = frame

            native_w, native_h = (raw_frame.shape[1], raw_frame.shape[0]) if raw_frame is not None else (1280, 720)

            # 2. Build camera feed cells
            camera_cells = []
            disconnected_count = 0

            for cam_id in range(num_cameras):
                is_connected = True
                # Check if simulated disconnect is active for Camera 1
                if cam_id == 1 and cam1_simulated_disconnect:
                    is_connected = False
                    disconnected_count += 1

                if is_connected:
                    if raw_frame is not None:
                        f = raw_frame.copy()
                        if cam_id > 0:
                            overlay = np.zeros_like(f)
                            overlay[:, :] = (15 * cam_id, 10 * cam_id, 0)
                            f = cv2.add(f, overlay)
                    else:
                        f = create_synthetic_frame(cam_id, width=native_w, height=native_h, tick=tick)

                    # Shutter flash
                    if flash_frames > 0:
                        overlay = f.copy()
                        cv2.rectangle(overlay, (0, 0), (f.shape[1], f.shape[0]), (0, 255, 255), -1)
                        f = cv2.addWeighted(f, 0.6, overlay, 0.4, 0)

                    # Draw Connection Status Badge (🟢 Green)
                    draw_status_badge(f, cam_id=cam_id, is_connected=True,
                                      resolution_text=f"{native_w}x{native_h}", fps=fps_display)
                    camera_cells.append(f)
                else:
                    # Draw Disconnected Alert Slot (🔴 Red)
                    f = create_disconnected_slot(cam_id, width=native_w, height=native_h)
                    draw_status_badge(f, cam_id=cam_id, is_connected=False)
                    camera_cells.append(f)

            if flash_frames > 0:
                flash_frames -= 1

            # 3. Assemble combined grid
            combined = build_camera_grid(camera_cells, max_w=1200, max_h=680)

            # 4. Global bottom status summary
            banner_h = 42
            banner = np.zeros((banner_h, combined.shape[1], 3), dtype=np.uint8)
            banner[:] = (18, 18, 24)
            cv2.line(banner, (0, 0), (combined.shape[1], 0), (45, 45, 60), 1)

            if disconnected_count > 0:
                status_txt = f"⚠ WARNING: {disconnected_count} camera(s) disconnected! Reconnect USB or press [D] to reset."
                status_col = COLOR_DISCONN
            else:
                status_txt = f"All {num_cameras} camera(s) connected & streaming normally."
                status_col = COLOR_LIVE

            # Status dot & text in bottom bar
            cv2.circle(banner, (20, banner_h // 2), 6, status_col, -1)
            cv2.putText(banner, status_txt, (35, banner_h // 2 + 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_col, 1, cv2.LINE_AA)

            help_txt = "[1-6] Cam Count | [D] Disconnect Cam 1 | [SPACE] Capture | [ESC] Quit"
            (hw, _), _ = cv2.getTextSize(help_txt, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
            cv2.putText(banner, help_txt, (combined.shape[1] - hw - 18, banner_h // 2 + 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (160, 160, 180), 1, cv2.LINE_AA)

            final_output = np.vstack([combined, banner])
            cv2.imshow(window_name, final_output)

            # 5. Keys
            key = cv2.waitKey(15) & 0xFF
            if key == 27 or cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                break

            # D: Toggle disconnect on Cam 1
            elif key in (ord('d'), ord('D')):
                cam1_simulated_disconnect = not cam1_simulated_disconnect
                state = "DISCONNECTED" if cam1_simulated_disconnect else "RECONNECTED"
                print(f" Camera 1 is now {state}")

            # SPACE: Flash capture
            elif key == 32:
                flash_frames = 6
                print(" Photo captured across all active cameras.")

            # 1 to 6: Camera count
            elif ord('1') <= key <= ord('6'):
                num_cameras = key - ord('0')
                print(f" Switched to {num_cameras} camera(s).")

    finally:
        if has_webcam:
            cap.release()
        cv2.destroyAllWindows()
        print("\nSimulator closed.")


if __name__ == "__main__":
    run_simulation()

