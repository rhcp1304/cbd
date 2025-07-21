import gradio as gr
import pandas as pd
import google.generativeai as genai
import os
import io
import contextlib
os.environ.setdefault("GOOGLE_API_KEY","AIzaSyBq2_GdMf0KhowSVSb0hn4Z_8B81kBewXY")
GEMINI_API_KEY = os.environ.get("GOOGLE_API_KEY", "YOUR_GEMINI_API_KEY")
if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
    print("WARNING: GOOGLE_API_KEY environment variable not set. Using placeholder. Please set it for Gemini to work.")
try:
    genai.configure(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"Error configuring Gemini API: {e}. Please check your API key.")

GEMINI_MODEL_NAME = 'gemini-2.5-flash-lite-preview-06-17'


def execute_python_code(code: str, df: pd.DataFrame) -> str:
    local_vars = {'df': df, 'pd': pd}
    old_stdout = io.StringIO()
    with contextlib.redirect_stdout(old_stdout):
        try:
            exec(code, {}, local_vars)
            return old_stdout.getvalue()
        except Exception as e:
            return f"Error during code execution: {e}\nCode:\n{code}"


def query_data_with_gemini_as_agent(file_path: str, user_query: str, model_name: str = GEMINI_MODEL_NAME):
    df = None
    read_success = False
    encodings_to_try = ['utf-8', 'latin1', 'ISO-8859-1', 'cp1252']
    log_messages = []

    def log_print(message):
        log_messages.append(message)
        print(message)

    for encoding in encodings_to_try:
        try:
            log_print(f"Attempting to read file '{file_path}' with encoding: '{encoding}'")
            df = pd.read_csv(file_path, encoding=encoding)
            read_success = True
            log_print(f"File successfully read with encoding: '{encoding}'")
            break
        except UnicodeDecodeError:
            log_print(f"Failed to read with encoding '{encoding}'. Trying next...")
        except FileNotFoundError:
            # Return empty strings for other outputs if file not found
            return f"Error: The file '{file_path}' was not found. Please ensure it's in the correct directory and spelled correctly.", "", "", ""
        except Exception as e:
            log_print(f"An unexpected error occurred while reading with encoding '{encoding}': {e}. Trying next...")

    if not read_success:
        return f"Error: Could not read the CSV file '{file_path}' with any of the attempted encodings. The file might be corrupted or have an unusual encoding.", "", "", ""

    df_info = io.StringIO()
    df.info(buf=df_info)
    df_info_str = df_info.getvalue()
    column_names = ", ".join(df.columns.tolist())
    sample_data_markdown = df.head(5).to_markdown(index=False)
    prompt_for_code_gen = f"""
    You are an AI assistant specialized in data analysis.
    You have access to a Pandas DataFrame named `df` loaded from a CSV file.
    The `pandas` library is available as `pd`.

    Here is information about the DataFrame:
    - Columns: {column_names}
    - Data types and non-null values (from df.info()):
    ```
    {df_info_str}
    ```
    - Sample rows:
    ```
    {sample_data_markdown}
    ```

    The user wants to analyze this data. Your task is to **write Python code** using Pandas to answer the user's question.

    **Important Rules:**
    1.  Only output the Python code. Do not include any explanation or extra text.
    2.  Make sure the code is executable and directly answers the question by printing the result.
    3.  If the question asks for a single value (e.g., average, sum, count), print only that value. Ensure numeric conversions are handled (e.g., `pd.to_numeric(df['Column'], errors='coerce')`).
    4.  If the question asks for a table or filtered data, print the DataFrame/Series to markdown using `.to_markdown(index=False)` if it's a DataFrame, or just print Series directly.
    5.  Use `df` as the DataFrame variable.
    6.  If you believe the question cannot be answered with the provided DataFrame, print a short message like "Cannot answer this question with the available data."

    **Crucial Clarifications for Specific Columns:**
    - For 'Docusign Date', consider it "completed" ONLY if the value is an actual date string (e.g., '18-Jul-25'). Exclude values like 'BD Pending', '-', 'Relocation', 'Conversion', or NaN.
    - For 'DD Completetion date', consider it "pending" ONLY if the value is the exact string 'Pending'. Exclude any other values, including dates, 'Conversion', 'Relocation', 'Dropped', 'SendBack', or NaN.
    - For any filter value, keep it case insensitive. e.g. 'Operational', 'operational' should be considered same

    User's Question: {user_query}
    """
    model = genai.GenerativeModel(model_name)
    log_print("Asking Gemini to generate Python code for the query...")
    generated_code = ""
    try:
        response_code_gen = model.generate_content(prompt_for_code_gen)
        generated_code = response_code_gen.text.strip()
        if generated_code.startswith("```python") and generated_code.endswith("```"):
            generated_code = generated_code[len("```python"): -len("```")].strip()
        elif generated_code.startswith("```") and generated_code.endswith("```"):
            generated_code = generated_code[len("```"): -len("```")].strip()
    except Exception as e:
        log_print(f"Error generating code from Gemini: {e}")
        return f"Error: Could not generate code from Gemini. {e}", "", "", ""

    log_print(f"\n--- Generated Code ---\n{generated_code}\n----------------------")

    log_print("Executing generated code...")
    execution_output = execute_python_code(generated_code, df.copy())
    log_print(f"\n--- Code Execution Output ---\n{execution_output}\n---------------------------")

    prompt_for_interpretation = f"""
    You previously generated Python code to analyze a dataset, and that code was executed.
    Here is the original user's question: "{user_query}"
    Here is the output from executing the Python code:
    ```
    {execution_output}
    ```
    Based on the original question and the code execution output, provide a concise and clear natural language answer to the user.
    If the output indicates an error or no data, explain that.
    """

    log_print("Asking Gemini to interpret the execution output...")
    final_answer = ""
    try:
        response_final_answer = model.generate_content(prompt_for_interpretation)
        final_answer = response_final_answer.text
    except Exception as e:
        log_print(f"Error interpreting output with Gemini: {e}")
        final_answer = f"Error: Could not get final interpretation from Gemini. {e}"

    return "\n".join(log_messages), generated_code, execution_output, final_answer

