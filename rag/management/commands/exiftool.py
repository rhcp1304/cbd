# myapp/management/commands/extract_video_gps_ocr.py

from django.core.management.base import BaseCommand, CommandError
import os
import pytesseract  # Needed to set the tesseract_cmd path
import ast  # Used for safely evaluating string tuples to actual tuples

# Import the core OCR extraction function from your utils module
from ...helpers.exiftool_helper import extract_data_from_video_ocr


class Command(BaseCommand):
    help = 'Extracts timestamp and GPS data from video frames using OCR on specified Regions of Interest.'

    def add_arguments(self, parser):
        parser.add_argument('video_path', type=str,
                            help='Absolute or relative path to the input video file (e.g., "C:\\path\\to\\video.mp4").')

        # Required argument: Latitude/Longitude ROI
        parser.add_argument('--lat-lon-roi', type=str, required=True,
                            help='Region of Interest for Latitude/Longitude as a string tuple "(x, y, w, h)". '
                                 'Example: --lat-lon-roi "(10, 800, 250, 30)"')

        # Optional argument: DateTime ROI
        parser.add_argument('--datetime-roi', type=str,
                            help='Region of Interest for DateTime as a string tuple "(x, y, w, h)". '
                                 'Example: --datetime-roi "(10, 750, 300, 30)"')

        # Optional argument: Path to Tesseract executable
        parser.add_argument('--tesseract-path', type=str,
                            help='Full path to the tesseract executable. '
                                 'Example for Windows: "C:\\Program Files\\Tesseract-OCR\\tesseract.exe"')

        # Optional: Limit number of frames to process for testing
        parser.add_argument('--max-frames', type=int, default=0,
                            help='Process a maximum number of frames (0 for all frames). Useful for testing.')

    def handle(self, *args, **options):
        video_path = options['video_path']
        lat_lon_roi_str = options['lat_lon_roi']
        datetime_roi_str = options['datetime_roi']
        tesseract_path = options['tesseract_path']
        # max_frames = options['max_frames'] # (Not implemented in helper yet, but useful future option)

        # --- Basic Validation ---
        if not os.path.exists(video_path):
            raise CommandError(f"Error: Video file not found at: '{video_path}'")

        # --- Set Tesseract Path ---
        if tesseract_path:
            try:
                # Ensure the path is correct and accessible for pytesseract
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
                self.stdout.write(self.style.SUCCESS(f"Tesseract executable path set to: '{tesseract_path}'"))
            except Exception as e:
                # Catch any error during path setting (e.g., invalid path, permissions)
                raise CommandError(
                    f"Error setting Tesseract path. Please check the path and Tesseract installation. Details: {e}")

        # --- Parse ROI Strings to Tuples ---
        lat_lon_roi_coords = None
        datetime_roi_coords = None

        try:
            # ast.literal_eval is safer than eval() for parsing string literals
            lat_lon_roi_coords = ast.literal_eval(lat_lon_roi_str)
            if not (isinstance(lat_lon_roi_coords, tuple) and len(lat_lon_roi_coords) == 4 and all(
                    isinstance(i, int) for i in lat_lon_roi_coords)):
                raise ValueError("ROI tuple must contain 4 integers.")
        except (ValueError, SyntaxError):
            raise CommandError(
                f"Invalid --lat-lon-roi format. Must be a tuple of 4 integers, e.g., \"(10, 20, 100, 50)\". Got: '{lat_lon_roi_str}'")

        if datetime_roi_str:
            try:
                datetime_roi_coords = ast.literal_eval(datetime_roi_str)
                if not (isinstance(datetime_roi_coords, tuple) and len(datetime_roi_coords) == 4 and all(
                        isinstance(i, int) for i in datetime_roi_coords)):
                    raise ValueError("ROI tuple must contain 4 integers.")
            except (ValueError, SyntaxError):
                raise CommandError(
                    f"Invalid --datetime-roi format. Must be a tuple of 4 integers, e.g., \"(10, 20, 100, 50)\". Got: '{datetime_roi_str}'")

        self.stdout.write(self.style.SUCCESS(f"Starting OCR data extraction from: '{video_path}'"))
        self.stdout.write(f"  Latitude/Longitude ROI: {lat_lon_roi_coords}")
        self.stdout.write(f"  DateTime ROI: {datetime_roi_coords if datetime_roi_coords else 'Not requested'}")

        # --- Call the OCR extraction helper function ---
        try:
            extracted_ocr_data = extract_data_from_video_ocr(
                video_path,
                lat_lon_roi_coords,
                datetime_roi_coords
            )

            # --- Output Results ---
            if extracted_ocr_data:
                self.stdout.write(self.style.SUCCESS("\n--- Extracted Data via OCR ---"))
                # Print a limited number of entries for console readability
                for entry in extracted_ocr_data[:20]:
                    self.stdout.write(f"Frame {entry['FrameNumber']}:")
                    self.stdout.write(f"  DateTime: {entry['DateTimeOCR']}")
                    # Use formatted string to explicitly show 'None' if parsing failed
                    self.stdout.write(
                        f"  Latitude: {entry['Latitude'] if entry['Latitude'] is not None else "'None' (Not Parsed)"}")
                    self.stdout.write(
                        f"  Longitude: {entry['Longitude'] if entry['Longitude'] is not None else "'None' (Not Parsed)"}")
                    self.stdout.write("--------------------")

                if len(extracted_ocr_data) > 20:
                    self.stdout.write(f"...and {len(extracted_ocr_data) - 20} more entries.")

                self.stdout.write(self.style.SUCCESS("--- OCR Extraction Complete ---"))
            else:
                self.stdout.write(self.style.WARNING(
                    "No data extracted. This could be due to incorrect ROIs, unreadable text, or an issue with the video file."))

        except RuntimeError as e:
            # Catch specific RuntimeErrors raised by the helper function (e.g., TesseractNotFoundError)
            raise CommandError(f"An OCR processing error occurred: {e}") from e
        except Exception as e:
            # Catch any other unexpected exceptions during the process
            raise CommandError(f"An unhandled error occurred during video OCR extraction: {e}") from e