import os
from flask import Flask, render_template, request, jsonify
import fitz  # PyMuPDF
import requests
import json
from flask import Response

app = Flask(__name__)

OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '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')  # Load API key from environment variables
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "deepseek/deepseek-r1:free"  # Change this if needed

# Function to extract text from PDF
def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text("text") + "\n"
    
    # Save extracted text to a file
    extracted_text_path = "extracted_text.txt"
    with open(extracted_text_path, "w", encoding="utf-8") as f:
        f.write(text)
    
    return text  # Return extracted text directly

# Function to generate script using OpenRouter API
def generate_script_from_text_and_topic(topic, format_length, extracted_text="", additional_context=""):
    prompt = f"""
    Generate a YouTube video script about the topic "{topic}" using the following context extracted from previous content:

    MPORTANT INSTRUCTIONS:

    — Absolutely no thinking process or reasoning should be shown in the output. Only the content provided below should be used — no background details, processing information, or model-specific understanding should appear in the final output.

    — Use of emojis is mandatory in the generated script. Ensure they are appropriately placed throughout the script, enriching the conversational tone.

    — Include average time stamps for when each section of the script should appear, such as the hook, body, specific titles in the body, and the call to action. This time distribution must be clear and precise.

    — The content you are working with is derived from someone else's video script, so do not include any personal data or references to the original content creator. The focus is on creating new content based on the structure of the script, not copying or linking back to the original creator.

    — Do not copy-paste any text verbatim from the provided script. You are allowed to use the format and structure for understanding how to generate scripts in a conversational style, but the output must be original and inspired by the structure, not duplicated.

    — Mention appropriate visuals that should appear on screen alongside each line of dialogue in the generated script. This should align with the content being discussed and should enrich the viewer’s experience.

    — For long and medium format scripts, stretch the body with full of information, told in a story-like manner. If the user selects medium, long, or short, ensure that the script reaches at least the minimum duration provided as input.
    
    Format: For short, medium, and long format bodies, ensure that the content is long enough to match the required duration when spoken. For short format (1-minute), the body should contain around 150-180 words, ensuring it fits comfortably within that timeframe at a neutral or slightly faster speaking pace. For medium format (10-minute), aim for 1,500-1,800 words, providing enough depth and information to sustain a 10-minute delivery. For long format (25-minute), the body should be approximately 3,500-4,200 words, ensuring it maintains a smooth flow and doesn’t feel rushed, with content that can be delivered at a neutral pace for the full 25 minutes. Adjust the word count according to the pace, but ensure it meets the required minimum for each format. Stritcly generate the script for **{format_length}** duration. 
    
    mention at end,
    **Tone & Style Notes:** which includes pace, visuals, language
        Like this as an example:  **Tone & Style Notes:**  
        - **Pace:** Fast, punchy edits matching the energy of the example scripts.  
        - **Visuals:** Mix AI-generated art close-ups, artists working with tech, and futuristic concepts.  
        - **Language:** Conversational, loaded with metaphors ("AI’s democratizing art"), rhetorical questions, and "insider" phrasing ("gatekeepers are sweating").  

    {f'Additional context: {additional_context}' if additional_context else ''}

    {extracted_text if extracted_text else 'No extracted text provided, generate based on topic alone.'}
    
    The script should include:
    - A **catchy hook** to grab attention at the beginning.
    - A **body** that explains the topic clearly and concisely.
    - A **call to action (CTA)** at the end to engage the audience.
    """
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 140000
    }
    
    response = requests.post(OPENROUTER_URL, json=payload, headers=headers, timeout=50)
    

    if response.status_code == 200:
        result = response.json()
        if "choices" in result:
            return result["choices"][0]["message"]["content"]
        else:
            return f"Error: Unexpected response format - {json.dumps(result, indent=2)}"
    else:
        return f"Error: {response.status_code} - {response.text}"

@app.route('/')
def welcome():
    return render_template('welcome.html')  # Serve the welcome page first

@app.route('/home')
def index():
    return render_template('index.html')  # Show the main page (HTML form)

@app.route("/creator")
def creator():
    return render_template("creator.html")


@app.route('/upload', methods=['POST'])
def upload_pdf():
    topic = request.form['topic']
    format_length = request.form['format']
    additional_context = request.form.get('additional_context', '')
    file = request.files.get('file')

    extracted_text = ""
    if file and file.filename.lower().endswith('.pdf'):
        if not os.path.exists("uploads"):
            os.makedirs("uploads")
        pdf_path = os.path.join("uploads", file.filename)
        file.save(pdf_path)
        extracted_text = extract_text_from_pdf(pdf_path)

    generated_script = generate_script_from_text_and_topic(topic, format_length, extracted_text, additional_context)

    def stream_script(script):
        """Generator function to stream the response"""
        for chunk in script.split("\n"):  # Send line by line
            yield chunk + "\n"
    
    return Response(stream_script(generated_script), content_type='text/plain')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
