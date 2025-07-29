import cv2

def get_roi_from_video_interactive(video_path, display_max_width=1280, display_max_height=720):
    """
    Interactively allows the user to navigate video frames and select Regions of Interest (ROIs).
    Resizes the frame for display to ensure the entire frame is visible, especially for high-res videos.

    Args:
        video_path (str): The path to the video file.
        display_max_width (int): Maximum width for the displayed frame.
        display_max_height (int): Maximum height for the displayed frame.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video file: {video_path}. Please check the path and file integrity.")
        return

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames == 0:
        print(f"Error: Video file {video_path} contains no frames.")
        cap.release()
        return

    # Get original video dimensions
    original_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    original_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    current_frame_idx = 0
    cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame_idx)

    print("--- Interactive ROI Selection Tool ---")
    print(f"Original Video Resolution: {original_width}x{original_height}")
    print(f"Display Window will be resized to fit within {display_max_width}x{display_max_height}")
    print("Press 'Right Arrow' (->) to go to the next frame.")
    print("Press 'Left Arrow' (<-) to go to the previous frame.")
    print("Press 's' to SELECT ROIs on the CURRENTLY displayed frame.")
    print("Press 'q' to QUIT and get the coordinates (after selection, or to exit).")
    print("--------------------------------------")

    selected_ll_roi = None
    selected_dt_roi = None

    window_name = "Select ROI - Navigate Frames (Resized for Display)"

    while True:
        cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame_idx)
        ret, frame = cap.read()

        if not ret:
            print(f"Reached end or error reading frame {current_frame_idx}. Looping back to start.")
            current_frame_idx = 0
            cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame_idx)
            ret, frame = cap.read()
            if not ret:
                print("Could not read any frames from video even after resetting.")
                break

        # --- Resize frame for display while maintaining aspect ratio ---
        # This is the key change to ensure the whole frame is visible
        scale_w = display_max_width / original_width
        scale_h = display_max_height / original_height
        scale_factor = min(scale_w, scale_h) # Use the smaller scale factor to fit both dimensions

        if scale_factor < 1: # Only resize if original is larger than max display size
            display_width = int(original_width * scale_factor)
            display_height = int(original_height * scale_factor)
            display_frame_for_selection = cv2.resize(frame, (display_width, display_height))
        else:
            display_frame_for_selection = frame.copy() # No resize needed, use original size copy

        # Add instructions and frame number to the displayed frame
        cv2.putText(display_frame_for_selection, f"Frame: {current_frame_idx}/{total_frames - 1}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2, cv2.LINE_AA)
        cv2.putText(display_frame_for_selection, "Arrows: Navigate, 's': Select ROI, 'q': Quit", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1, cv2.LINE_AA)

        cv2.imshow(window_name, display_frame_for_selection)

        key = cv2.waitKey(0) & 0xFF

        if key == ord('q'):
            break
        elif key == 2 or key == 2424832: # Left arrow key code
            current_frame_idx = max(0, current_frame_idx - 1)
        elif key == 3 or key == 2555904: # Right arrow key code
            current_frame_idx = min(total_frames - 1, current_frame_idx + 1)
        elif key == ord('s'):
            cv2.destroyWindow(window_name) # Close the navigation window temporarily

            print(f"\nSelecting ROIs on Frame {current_frame_idx}...")
            print("Select the Region of Interest (ROI) for Latitude/Longitude. Drag a rectangle and press ENTER/SPACE.")
            # Important: selectROI operates on the 'display_frame_for_selection'
            ll_roi_scaled = cv2.selectROI("Select Lat/Lon ROI (Precise!)", display_frame_for_selection, fromCenter=False, showCrosshair=True)
            cv2.destroyWindow("Select Lat/Lon ROI (Precise!)")

            print("Select the Region of Interest (ROI) for DateTime. Drag a rectangle and press ENTER/SPACE.")
            dt_roi_scaled = cv2.selectROI("Select DateTime ROI (Precise!)", display_frame_for_selection, fromCenter=False, showCrosshair=True)
            cv2.destroyWindow("Select DateTime ROI (Precise!)")

            # --- Scale ROI coordinates back to original video resolution ---
            # This is critical because your main processing uses original resolution frames
            if scale_factor < 1:
                selected_ll_roi = tuple(int(coord / scale_factor) for coord in ll_roi_scaled)
                selected_dt_roi = tuple(int(coord / scale_factor) for coord in dt_roi_scaled)
            else:
                selected_ll_roi = ll_roi_scaled
                selected_dt_roi = dt_roi_scaled

            print(f"\nROIs selected on Frame {current_frame_idx} (scaled to original video resolution).")
            print("You can now press 'q' to quit and see the final results, or continue navigating.")

            cv2.imshow(window_name, display_frame_for_selection) # Reopen display window

    cap.release()
    cv2.destroyAllWindows()

    if selected_ll_roi and selected_dt_roi:
        print(f"\n--- Final Selected ROIs (for original video resolution) ---")
        print(f"Latitude/Longitude ROI: {selected_ll_roi}")
        print(f"DateTime ROI: {selected_dt_roi}")
        print("\nUse these NEW coordinates in your Django management command (x, y, w, h).")
        print("Example: --lat-lon-roi \"(X, Y, W, H)\" --datetime-roi \"(X, Y, W, H)\"")
    else:
        print("\nNo ROIs were selected or the operation was cancelled before selection.")

# --- Run this script ---
# IMPORTANT: Replace 'C:/Users/Ankit.Anand/Downloads/timestamp_video.mp4' with the actual path to your video file.
if __name__ == '__main__':
    # You can adjust display_max_width and display_max_height if your screen is smaller or larger
    get_roi_from_video_interactive('C:/Users/Ankit.Anand/Downloads/timestamp_video.mp4',
                                   display_max_width=1280, display_max_height=720) # Common display size