import google.generativeai as genai
from google.generativeai import GenerationConfig
import time
import os
from google.generativeai.types.file_types import File
from google.api_core import exceptions  # Import the exceptions module

genai.configure(api_key="AIzaSyD0nx9rH7HhQZDpJrY0hOaOR9Xok4r-liM")
model = genai.GenerativeModel('gemini-2.5-flash')

video_paths = [

    r"C:\Users\Ankit.Anand\Downloads\output00.mp4",
    r"C:\Users\Ankit.Anand\Downloads\output01.mp4",
    r"C:\Users\Ankit.Anand\Downloads\output02.mp4",
    r"C:\Users\Ankit.Anand\Downloads\output03.mp4",
]

all_analyses = []
output_filename_consolidated = "meeting_analysis_report.txt"
output_filename_detailed = "detailed_meeting_analysis.txt"

try:
    with open(output_filename_detailed, "w", encoding="utf-8") as f:
        f.write("--- Detailed Team Meeting Segment Analysis Report ---\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Date of analysis: {time.strftime('%Y-%m-%d %H:%M:%S %Z')}\n\n")
except Exception as e:
    print(f"Error initializing detailed report file '{output_filename_detailed}': {e}")


for i, video_path in enumerate(video_paths):
    print(f"Processing video part {i + 1}: {video_path}")
    uploaded_file = None

    try:

        with open(video_path, "rb") as video_file:
            uploaded_file = genai.upload_file(video_file, mime_type="video/mp4")
        print(f"Uploaded file ID: {uploaded_file.name}, URI: {uploaded_file.uri}")

        start_wait_time = time.time()
        wait_timeout = 300

        FileStateEnum = uploaded_file.state.__class__

        while uploaded_file.state == FileStateEnum.PROCESSING:
            if time.time() - start_wait_time > wait_timeout:
                print(f"File processing timed out for {video_path}. Skipping this part.")
                # Mark as FAILED to ensure it's skipped later and deleted in finally block
                uploaded_file = File(name=uploaded_file.name, uri=uploaded_file.uri, state=FileStateEnum.FAILED)
                break
            print("File is still processing, waiting...")
            time.sleep(10)
            uploaded_file = genai.get_file(uploaded_file.name)

        if uploaded_file.state == FileStateEnum.FAILED:
            print(f"File processing failed for {video_path}. Skipping this part.")
            continue


        prompt = f"""
        This is part {i + 1} of a team meeting recording.
        Please analyze this segment and provide following for each of the properties:
        1. Timestamp (start and end) of the discussion of the property
        2. A summary of the key topics discussed.
        3. Any action items, task assigned or decisions made , with approximate timestamps if possible.
        4. Identify the main speakers and their primary contributions with timestamps.
        5. Provide the data about - Site Name | Store Size | Signage | Frontage | Beam to bottom height | Trade Area | Geoiq Proto | Rent | Ops Proto
        6. Provide the final decision made on the property - approved, dropped/rejected, conditionally approved, on hold
        
        """

        contents = [
            prompt,
            uploaded_file
        ]


        response_received = False
        retries = 0
        max_retries = 5

        while not response_received and retries < max_retries:
            try:
                response = model.generate_content(
                    contents,
                    generation_config=GenerationConfig(temperature=0.4),
                    request_options={"timeout": 900}
                )
                response_received = True
            except exceptions.ResourceExhausted as e:
                retries += 1
                delay_seconds = 15
                print(f"Quota exceeded. Retrying in {delay_seconds} seconds... (Attempt {retries}/{max_retries})")
                time.sleep(delay_seconds)
            except Exception as e:

                print(f"An unexpected error occurred during content generation for {video_path}: {e}")
                break

        if not response_received:
            print(f"Failed to get response for part {i + 1} after {max_retries} retries due to quota issues.")
            continue


        if response.text:
            segment_analysis = {
                "part": i + 1,
                "filename": os.path.basename(video_path),
                "summary": response.text
            }
            all_analyses.append(segment_analysis)
            print(f"Analysis for part {i + 1}:\n{response.text}\n")

            try:
                with open(output_filename_detailed, "a", encoding="utf-8") as f:
                    f.write(f"\n--- Analysis for Part {i + 1} ({os.path.basename(video_path)}) ---\n")
                    f.write(response.text)
                    f.write("\n" + "=" * 50 + "\n")
                print(f"Detailed analysis for part {i + 1} written to '{output_filename_detailed}'")
            except Exception as e:
                print(f"Error writing detailed analysis for part {i + 1} to file: {e}")


        else:
            print(f"Warning: No text content received for part {i + 1}.")

    except Exception as e:
        print(f"An error occurred while processing {video_path}: {e}")
    finally:

        if uploaded_file and uploaded_file.name:
            try:
                genai.delete_file(uploaded_file.name)
                print(f"Deleted file {uploaded_file.name} from Files API.")
            except Exception as e:
                print(f"Error deleting file {uploaded_file.name}: {e}")

final_report_content = ""
if all_analyses:
    combined_text = "\n\n".join(
        [f"--- Part {analysis['part']} ({analysis['filename']}) ---\n{analysis['summary']}" for analysis in
         all_analyses])

    final_prompt = f"""
    Here are the analyses of multiple segments from a team meeting.
    Please provide a comprehensive, overall summary of the entire meeting,
    identify all key action items across all parts, and list the main decisions.
    Do it property wise and make sure to provide the data about - Site Name | Store Size | Signage | Frontage | Beam to bottom height | Trade Area | Geoiq Proto | Rent | Ops Proto


    Combined Segment Analyses:
    {combined_text}
    """

    print("\n--- Generating final comprehensive analysis ---")
    final_response_received = False
    final_retries = 0
    max_final_retries = 3

    while not final_response_received and final_retries < max_final_retries:
        try:
            final_response = model.generate_content(final_prompt, generation_config=GenerationConfig(temperature=0.2),
                                                    request_options={"timeout": 900})
            final_report_content = final_response.text
            final_response_received = True
        except exceptions.ResourceExhausted as e:
            final_retries += 1
            delay_seconds = 15
            print(
                f"Final summary quota exceeded. Retrying in {delay_seconds} seconds... (Attempt {final_retries}/{max_final_retries})")
            time.sleep(delay_seconds)
        except Exception as e:
            print(f"An unexpected error occurred during final summary generation: {e}")
            break

    if not final_response_received:
        final_report_content = "Failed to generate comprehensive analysis after retries due to quota issues."

    print(final_report_content)
else:
    final_report_content = "No analyses were successfully generated for any video segments."
    print(final_report_content)

try:
    with open(output_filename_consolidated, "w", encoding="utf-8") as f:
        f.write("Team Meeting Analysis Report (Consolidated)\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Date of analysis: {time.strftime('%Y-%m-%d %H:%M:%S %Z')}\n\n")
        f.write(final_report_content)
    print(f"\nConsolidated analysis report successfully written to '{output_filename_consolidated}'")
except Exception as e:
    print(f"Error writing consolidated report to file '{output_filename_consolidated}': {e}")

