# myapp/utils/video_ocr_processor.py

import cv2
import pytesseract
import numpy as np
import re
from datetime import datetime

# IMPORTANT: Do NOT set pytesseract.pytesseract.tesseract_cmd here.
# It is set by the Django management command based on the --tesseract-path argument.
# If you run this file directly for testing (outside Django), you MUST uncomment and set the path here:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Users\Ankit.Anand\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'


def preprocess_roi(roi_image):
    """
    Applies common image processing steps to improve OCR accuracy on text regions.
    Assumes white text on a dark background in the original ROI.

    Args:
        roi_image (numpy.ndarray): The region of interest image (BGR format).

    Returns:
        numpy.ndarray: The preprocessed binary image (black text on white background)
                       ready for Tesseract OCR.
    """
    gray_roi = cv2.cvtColor(roi_image, cv2.COLOR_BGR2GRAY)

    # Apply Otsu's thresholding to convert the grayscale image to a binary (black and white) image.
    # THRESH_BINARY + THRESH_OTSU automatically determines an optimal threshold value.
    # For white text on a dark background, this typically results in white text on a black background.
    _, thresh_roi = cv2.threshold(gray_roi, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Invert the colors: Tesseract generally performs better when the text is black
    # and the background is white.
    thresh_roi_inverted = cv2.bitwise_not(thresh_roi)

    # --- Optional Advanced Preprocessing (uncomment and experiment if needed) ---
    # These can help with broken or bleeding characters, but can also degrade results
    # if applied too aggressively or inappropriately.

    # Dilation: Makes white regions (text in the inverted image) thicker. Useful for thin or broken characters.
    # kernel_dilate = np.ones((2,2), np.uint8) # Small kernel for minimal effect
    # thresh_roi_inverted = cv2.dilate(thresh_roi_inverted, kernel_dilate, iterations=1)

    # Erosion: Makes white regions (text in the inverted image) thinner. Useful for thick or bleeding characters.
    # kernel_erode = np.ones((2,2), np.uint8) # Small kernel for minimal effect
    # thresh_roi_inverted = cv2.erode(thresh_roi_inverted, kernel_erode, iterations=1)

    # Gaussian Blur: Can help remove small noise/speckles before thresholding, but can also blur text.
    # gray_roi = cv2.GaussianBlur(gray_roi, (3, 3), 0) # Apply before thresholding

    return thresh_roi_inverted


def parse_lat_lon_from_single_string(text):
    """
    Parses a string containing both latitude and longitude into separate float values.
    Handles various formats including optional degree symbols, N/S/E/W indicators,
    and flexible spacing/separators.

    Args:
        text (str): The OCR extracted string (e.g., "12.91036°N, 77.64468°E").

    Returns:
        tuple: (latitude_float, longitude_float) if parsing is successful,
               otherwise (None, None).
    """
    # Regex to capture two floating-point numbers with optional degree symbol and N/S/E/W indicators.
    # Group 1: First number (latitude value)
    # Group 2: Latitude direction (N/S)
    # Group 3: Second number (longitude value)
    # Group 4: Longitude direction (E/W)
    # `\s*°?\s*` allows for optional spaces and degree symbols.
    # `[,\s]*` allows for comma or spaces as a separator between lat/lon.
    match = re.search(r'([-+]?\d+\.\d+)\s*°?\s*([NSns])?[,\s]*([-+]?\d+\.\d+)\s*°?\s*([EWew])?', text, re.IGNORECASE)

    if match:
        try:
            lat_val = float(match.group(1))
            lat_dir = match.group(2)
            lon_val = float(match.group(3))
            lon_dir = match.group(4)

            # Adjust latitude sign based on direction (South is negative)
            if lat_dir and lat_dir.upper() == 'S':
                lat_val = -abs(lat_val)
            else: # Default to North if not 'S' (or no direction given, assume N)
                lat_val = abs(lat_val)

            # Adjust longitude sign based on direction (West is negative)
            if lon_dir and lon_dir.upper() == 'W':
                lon_val = -abs(lon_val)
            else: # Default to East if not 'W' (or no direction given, assume E)
                lon_val = abs(lon_val)

            return lat_val, lon_val
        except (ValueError, TypeError):
            # Log or print a debug message if float conversion fails for malformed OCR text
            # print(f"DEBUG: Failed to convert parts to float: {match.groups()} from text: '{text}'")
            return None, None
    else:
        # Log or print a debug message if the regex does not find a match
        # print(f"DEBUG: Regex did not match for text: '{text}'")
        pass
    return None, None


def extract_data_from_video_ocr(video_path, lat_lon_roi_coords, datetime_roi_coords=None):
    """
    Extracts timestamp, latitude, and longitude data from a video file by performing
    Optical Character Recognition (OCR) on specified Regions of Interest (ROIs).

    Args:
        video_path (str): The full path to the input video file.
        lat_lon_roi_coords (tuple): A tuple (x, y, w, h) defining the ROI for
                                     combined Latitude and Longitude text.
        datetime_roi_coords (tuple, optional): A tuple (x, y, w, h) defining the ROI
                                             for DateTime text. If None, DateTime is not extracted.

    Returns:
        list: A list of dictionaries, where each dictionary represents data for a frame.
              Each dictionary contains:
              'FrameNumber' (int),
              'DateTimeOCR' (str, or "N/A" if not extracted/parsed),
              'Latitude' (float or None),
              'Longitude' (float or None).
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}. Please check path and permissions.")

    extracted_data = []
    frame_count = 0

    # Validate ROI coordinate formats at the start
    if not (isinstance(lat_lon_roi_coords, tuple) and len(lat_lon_roi_coords) == 4 and all(isinstance(i, int) for i in lat_lon_roi_coords)):
        raise ValueError("Latitude/Longitude ROI coordinates must be a tuple of 4 integers (x, y, w, h).")
    if datetime_roi_coords is not None and not (isinstance(datetime_roi_coords, tuple) and len(datetime_roi_coords) == 4 and all(isinstance(i, int) for i in datetime_roi_coords)):
        raise ValueError("DateTime ROI coordinates must be a tuple of 4 integers (x, y, w, h) or None.")


    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break # End of video or error reading frame

            frame_count += 1
            current_lat = None
            current_lon = None
            current_datetime_str = "N/A" # Default value if datetime not extracted or parsed

            frame_h, frame_w = frame.shape[:2]

            # --- Latitude & Longitude Extraction ---
            x_ll, y_ll, w_ll, h_ll = lat_lon_roi_coords
            # Check if Lat/Lon ROI is fully within current frame boundaries
            if x_ll >= 0 and y_ll >= 0 and x_ll + w_ll <= frame_w and y_ll + h_ll <= frame_h:
                lat_lon_roi = frame[y_ll : y_ll + h_ll, x_ll : x_ll + w_ll]
                thresh_lat_lon_roi = preprocess_roi(lat_lon_roi)

                # --- DEBUGGING DISPLAY: Show the preprocessed ROI image for Lat/Lon ---
                cv2.imshow("Thresh Lat/Lon ROI", thresh_lat_lon_roi)
                # ---------------------------------------------------------------------

                # Perform OCR on the preprocessed Latitude/Longitude ROI
                ll_text = pytesseract.image_to_string(
                    thresh_lat_lon_roi,
                    # psm 7: Treat the image as a single text line.
                    # tessedit_char_whitelist: Restrict Tesseract to these characters for better accuracy.
                    config='--psm 7 -c tessedit_char_whitelist=0123456789.-,°NSEW'
                ).strip() # .strip() removes leading/trailing whitespace and newlines
                current_lat, current_lon = parse_lat_lon_from_single_string(ll_text)

                # --- DEBUGGING PRINT: Show raw OCR text and parsed values in console ---
                print(f"Frame {frame_count}: Lat/Lon OCR Text: '{ll_text}', Parsed Lat: {current_lat}, Parsed Lon: {current_lon}")
                # -----------------------------------------------------------------------

            else:
                print(f"Warning: Lat/Lon ROI ({lat_lon_roi_coords}) out of bounds for frame {frame_count} (Frame dimensions: {frame_w}x{frame_h}). Skipping Lat/Lon extraction.")

            # --- DateTime Extraction (Optional) ---
            if datetime_roi_coords:
                x_dt, y_dt, w_dt, h_dt = datetime_roi_coords
                # Check if DateTime ROI is fully within current frame boundaries
                if x_dt >= 0 and y_dt >= 0 and x_dt + w_dt <= frame_w and y_dt + h_dt <= frame_h:
                    datetime_roi = frame[y_dt : y_dt + h_dt, x_dt : x_dt + w_dt]
                    thresh_datetime_roi = preprocess_roi(datetime_roi)

                    # --- DEBUGGING DISPLAY: Show the preprocessed ROI image for DateTime ---
                    cv2.imshow("Thresh DateTime ROI", thresh_datetime_roi)
                    # ---------------------------------------------------------------------

                    # Perform OCR on the preprocessed DateTime ROI
                    dt_text = pytesseract.image_to_string(
                        thresh_datetime_roi,
                        # psm 7: Treat as single text line.
                        # Whitelist for common date/time characters including space and AM/PM.
                        config='--psm 7 -c tessedit_char_whitelist=0123456789-/:. AMPM'
                    ).strip()
                    if dt_text:
                        current_datetime_str = dt_text

                    # --- DEBUGGING PRINT: Show raw OCR text for DateTime in console ---
                    print(f"Frame {frame_count}: DateTime OCR Text: '{current_datetime_str}'")
                    # -------------------------------------------------------------------

                else:
                    print(f"Warning: DateTime ROI ({datetime_roi_coords}) out of bounds for frame {frame_count} (Frame dimensions: {frame_w}x{frame_h}). Skipping datetime extraction.")

            # Append all extracted (or 'None'/'N/A') data for the current frame
            extracted_data.append({
                'FrameNumber': frame_count,
                'DateTimeOCR': current_datetime_str,
                'Latitude': current_lat,
                'Longitude': current_lon
            })

            # --- OpenCV waitKey for interactive debugging ---
            # `cv2.waitKey(1)` waits for 1 millisecond. If 'q' is pressed, it breaks the loop.
            # This allows the imshow windows to refresh and keeps the script responsive.
            # Press 'q' key in one of the imshow windows to stop processing and close windows.
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except pytesseract.TesseractNotFoundError:
        # Specific error for Tesseract executable not found
        raise RuntimeError("Tesseract is not installed or not found in your PATH. "
                           "Please install Tesseract OCR engine and/or ensure the --tesseract-path argument is correct.")
    except Exception as e:
        # Catch any other unexpected exceptions during the OCR process
        raise RuntimeError(f"An unexpected error occurred during OCR extraction: {e}") from e
    finally:
        # Ensure video capture object is released and all OpenCV windows are closed
        if cap.isOpened():
            cap.release()
        cv2.destroyAllWindows() # Close all active OpenCV GUI windows

    return extracted_data