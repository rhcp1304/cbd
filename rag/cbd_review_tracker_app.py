import os
import gradio as gr
from helpers.ask_gemini_helper import query_data_with_gemini_as_agent


default_csv_path = 'C:/Users/Ankit.Anand/Downloads/FY26-CBD Review Tracker.csv'
if not os.path.exists(default_csv_path):
    default_csv_path = "path/to/your/FY26-CBD Review Tracker.csv"
    print(f"Default CSV path '{default_csv_path}' not found. Please update the path in the UI.")

with gr.Blocks(theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
        # 📊 Data Query Agent with Gemini and Pandas
        Enter your CSV file path and a natural language query to get insights from your data.
        The agent will generate and execute Python code using Pandas, then interpret the results.
        **Remember to set your `GOOGLE_API_KEY` environment variable!**
        """
    )

    with gr.Row():
        with gr.Column(scale=1):
            csv_file_path_input = gr.Textbox(
                label="CSV File Path",
                placeholder="e.g., C:/Users/YourUser/Documents/my_data.csv",
                value=default_csv_path,
                interactive=True,
                elem_id="csv_path_input"
            )
            user_query_input = gr.Textbox(
                label="Your Natural Language Query",
                placeholder="e.g., Show me the total sales for products in the 'Electronics' category.",
                lines=3,
                interactive=True,
                elem_id="user_query_input"
            )
            submit_button = gr.Button("🚀 Run Query", variant="primary", elem_id="run_query_button")

        with gr.Column(scale=2):
            final_answer_output = gr.Markdown(
                "## 💡 Final Answer:",
                elem_id="final_answer_output"
            )

    with gr.Accordion("📋 Process Logs", open=False):
        logs_output = gr.Textbox(
            label="Logs",
            lines=10,
            interactive=False,
            elem_id="logs_output"
        )

    with gr.Accordion("💻 Generated Python Code", open=False):
        generated_code_output = gr.Code(
            label="Code",
            language="python",
            lines=15,
            interactive=False,
            elem_id="generated_code_output"
        )

    with gr.Accordion("📊 Code Execution Output", open=False):
        execution_output_display = gr.Textbox(
            label="Execution Result",
            lines=15,
            interactive=False,
            elem_id="execution_output_display"
        )

    submit_button.click(
        fn=query_data_with_gemini_as_agent,
        inputs=[csv_file_path_input, user_query_input],
        outputs=[logs_output, generated_code_output, execution_output_display, final_answer_output]
    )

demo.css = """
    #csv_path_input, #user_query_input {
        border-radius: 8px;
        padding: 10px;
    }
    #run_query_button {
        border-radius: 12px;
        font-size: 1.1em;
        padding: 10px 20px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
    }
    #final_answer_output {
        background-color: #f0f8ff; /* Light blue background */
        border-left: 5px solid #4CAF50; /* Green border */
        padding: 15px;
        border-radius: 8px;
        margin-top: 20px;
        font-size: 1.1em;
    }
    .gradio-container {
        max-width: 1200px;
        margin: auto;
        padding: 20px;
    }
    .gr-accordion {
        margin-top: 15px;
        border-radius: 8px;
        overflow: hidden; /* Ensures rounded corners apply to content */
    }
"""

demo.launch()
