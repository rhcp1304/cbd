import google.generativeai as genai
from google.generativeai import GenerationConfig
import time
import os
from google.generativeai.types.file_types import File
from google.api_core import exceptions  # Import the exceptions module

genai.configure(api_key="AIzaSyCxTCYQO7s23L33kC4Io4G-i1p1ytD-OiI")
model = genai.GenerativeModel('gemini-2.5-flash')

video_paths = [
    r"C:\Users\Ankit.Anand\Desktop\team_meeting_clips\meeting_clip_000.mp4",
    r"C:\Users\Ankit.Anand\Desktop\team_meeting_clips\meeting_clip_001.mp4",
    r"C:\Users\Ankit.Anand\Desktop\team_meeting_clips\meeting_clip_002.mp4",
    r"C:\Users\Ankit.Anand\Desktop\team_meeting_clips\meeting_clip_003.mp4",
    r"C:\Users\Ankit.Anand\Desktop\team_meeting_clips\meeting_clip_004.mp4",
    r"C:\Users\Ankit.Anand\Desktop\team_meeting_clips\meeting_clip_005.mp4",
    r"C:\Users\Ankit.Anand\Desktop\team_meeting_clips\meeting_clip_006.mp4",
    r"C:\Users\Ankit.Anand\Desktop\team_meeting_clips\meeting_clip_007.mp4",
    r"C:\Users\Ankit.Anand\Desktop\team_meeting_clips\meeting_clip_008.mp4",
    r"C:\Users\Ankit.Anand\Desktop\team_meeting_clips\meeting_clip_009.mp4",
    r"C:\Users\Ankit.Anand\Desktop\team_meeting_clips\meeting_clip_010.mp4",
    r"C:\Users\Ankit.Anand\Desktop\team_meeting_clips\meeting_clip_011.mp4",
    r"C:\Users\Ankit.Anand\Desktop\team_meeting_clips\meeting_clip_012.mp4",
    r"C:\Users\Ankit.Anand\Desktop\team_meeting_clips\meeting_clip_013.mp4",
    r"C:\Users\Ankit.Anand\Desktop\team_meeting_clips\meeting_clip_014.mp4",
    r"C:\Users\Ankit.Anand\Desktop\team_meeting_clips\meeting_clip_015.mp4",
    r"C:\Users\Ankit.Anand\Desktop\team_meeting_clips\meeting_clip_016.mp4",
    r"C:\Users\Ankit.Anand\Desktop\team_meeting_clips\meeting_clip_017.mp4",
    r"C:\Users\Ankit.Anand\Desktop\team_meeting_clips\meeting_clip_018.mp4",
    r"C:\Users\Ankit.Anand\Desktop\team_meeting_clips\meeting_clip_019.mp4",
    r"C:\Users\Ankit.Anand\Desktop\team_meeting_clips\meeting_clip_020.mp4",
    r"C:\Users\Ankit.Anand\Desktop\team_meeting_clips\meeting_clip_021.mp4",
    r"C:\Users\Ankit.Anand\Desktop\team_meeting_clips\meeting_clip_022.mp4"

]

all_analyses = []
output_filename = "meeting_analysis_report.txt"

for i, video_path in enumerate(video_paths):
    print(f"Processing video part {i + 1}: {video_path}")
    uploaded_file = None  # Initialize uploaded_file outside try for proper scope
    try:
        with open(video_path, "rb") as video_file:
            uploaded_file = genai.upload_file(video_file, mime_type="video/mp4")
        print(f"Uploaded file ID: {uploaded_file.name}, URI: {uploaded_file.uri}")

        start_wait_time = time.time()
        wait_timeout = 300  # Wait for 5 minutes max for file processing

        FileStateEnum = uploaded_file.state.__class__

        while uploaded_file.state == FileStateEnum.PROCESSING:
            if time.time() - start_wait_time > wait_timeout:
                print(f"File processing timed out for {video_path}. Skipping this part.")
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
        Please analyze this segment and provide:
        1. A summary of the key topics discussed in this specific part.
        2. Any action items or decisions made in this specific part, with approximate timestamps if possible.
        3. Identify the main speakers in this part and their primary contributions.
        """

        contents = [
            prompt,
            uploaded_file
        ]

        # --- Implement retry logic for generate_content ---
        response_received = False
        retries = 0
        max_retries = 5  # Or adjust based on your needs

        while not response_received and retries < max_retries:
            try:
                response = model.generate_content(
                    contents,
                    generation_config=GenerationConfig(temperature=0.4),
                    request_options={"timeout": 900}
                )
                response_received = True  # If successful, exit loop
            except exceptions.ResourceExhausted as e:
                retries += 1
                delay_seconds = 15  # As suggested by the error message
                print(f"Quota exceeded. Retrying in {delay_seconds} seconds... (Attempt {retries}/{max_retries})")
                time.sleep(delay_seconds)
            except Exception as e:
                # Catch other potential errors here and break or log
                print(f"An unexpected error occurred during content generation: {e}")
                break

        if not response_received:
            print(f"Failed to get response for part {i + 1} after {max_retries} retries due to quota issues.")
            continue  # Skip to next video if all retries fail

        # --- End of retry logic ---

        if response.text:
            segment_analysis = {
                "part": i + 1,
                "filename": os.path.basename(video_path),
                "summary": response.text
            }
            all_analyses.append(segment_analysis)
            print(f"Analysis for part {i + 1}:\n{response.text}\n")
        else:
            print(f"Warning: No text content received for part {i + 1}.")

    except Exception as e:  # Catch errors during upload or initial processing
        print(f"An error occurred while processing {video_path}: {e}")
    finally:
        # Ensure file is deleted even if analysis fails or times out
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

    Combined Segment Analyses:
    {combined_text}
    """

    print("\n--- Generating final comprehensive analysis ---")
    final_response_received = False
    final_retries = 0
    max_final_retries = 3  # Less retries for the final summary

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
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write("Team Meeting Analysis Report\n")
        f.write("=" * 30 + "\n\n")
        f.write(f"Date of analysis: {time.strftime('%Y-%m-%d %H:%M:%S %Z')}\n\n")
        f.write(final_report_content)
    print(f"\nAnalysis report successfully written to '{output_filename}'")
except Exception as e:
    print(f"Error writing report to file '{output_filename}': {e}")