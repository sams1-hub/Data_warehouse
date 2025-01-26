import os
import re
from collections import Counter
from tkinter import Tk, filedialog
from llamaapi import LlamaAPI  # Import the LlamaAPI client

# Step 1: Allow user to select API key file
def select_api_key_file():
    """Open a file dialog to let the user select the API key file."""
    try:
        Tk().withdraw()  # Hide the root window
        file_path = filedialog.askopenfilename(
            title="Select API Key File",
            #filetypes=[("Text Files", "*.txt")]
        )
        if not file_path:
            raise ValueError("No file selected.")
        
        with open(file_path, "r") as file:
            api_key = file.read().strip()
            if not api_key:
                raise ValueError("The selected file is empty.")
        
        print("API key loaded successfully.")
        return api_key
    except Exception as e:
        print(f"Error loading API key: {e}")
        return None

# Step 2: Enhanced Information Extraction
def extract_important_details(text):
    extraction_patterns = {
        "dates": r"\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4})\b",
        "emails": r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b",
        "phone_numbers": r"\b(?:\+?(\d{1,3})[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
        "urls": r"\bhttps?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+\b",
        "important_terms": r"\b(?:urgent|critical|deadline|action required|important)\b",
        "entities": r"\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b"  # Simple named entity recognition
    }

    extracted_data = {}
    try:
        for key, pattern in extraction_patterns.items():
            matches = re.findall(pattern, text, flags=re.IGNORECASE)
            extracted_data[key] = list(set(matches))  # Remove duplicates

        # Add word frequency analysis
        words = re.findall(r'\b\w{4,}\b', text.lower())
        extracted_data["word_frequencies"] = Counter(words).most_common(10)
        
        return extracted_data
    except Exception as e:
        print(f"Extraction Error: {e}")
        return {}

# Step 3: Llama API Integration
def summarize_with_llama(api_key, input_text):
    """Send the input text to the Llama API for summarization."""
    try:
        # Initialize the LlamaAPI client
        llama = LlamaAPI(api_key)

        # Define the API request payload
        api_request_json = {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Summarize the following text in 2-3 sentences:\n\n{input_text}"}
            ],
            "max_tokens": 100,  # Adjust based on your needs
            "temperature": 0.7,  # Adjust for creativity vs. determinism
        }

        # Call the Llama API
        response = llama.run(api_request_json)

        # Extract the generated summary
        if response and response.get("choices"):
            return response["choices"][0]["message"]["content"]
        else:
            print("No summary generated.")
            return None
    except Exception as e:
        print(f"Llama API Error: {e}")
        return None

# Step 4: Save Analysis Results
def save_analysis(results, output_file="analysis_results.md"):
    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, "w") as f:
            # Write extracted entities
            f.write("# Extracted Information Analysis\n\n")
            for category, items in results["extracted"].items():
                if items:
                    f.write(f"## {category.replace('_', ' ').title()}\n")
                    for item in items:
                        f.write(f"- {item}\n")
                    f.write("\n")
            
            # Write AI analysis
            if results.get("ai_analysis"):
                f.write("# Llama AI Analysis\n")
                f.write(results["ai_analysis"])
            
            print(f"Analysis saved successfully to {output_file}")
            return True
    except Exception as e:
        print(f"File Save Error: {e}")
        return False

# Main Execution
if __name__ == "__main__":
    # Example text with various information types
    input_text = """
    Project Update - Q4 2024
    Important meeting scheduled for 15/12/2023 with Mr. John Smith from Acme Corp (contact: john.smith@acme.com).
    Deadline for proposal submission: December 20, 2023.
    Urgent: Review required for document at https://company.com/docs/q4-plan
    Contact support team: +1 (555) 123-4567 or support@company.com
    Key locations: New York Office, London Branch
    """
    
    # Step 1: Let the user select the API key file
    api_key = select_api_key_file()
    if not api_key:
        print("API key is required to proceed.")
        exit(1)
    
    # Step 2: Extract information
    extracted_data = extract_important_details(input_text)
    
    # Step 3: Get AI analysis using Llama API
    ai_analysis = summarize_with_llama(api_key, input_text)
    
    if ai_analysis:
        results = {
            "extracted": extracted_data,
            "ai_analysis": ai_analysis
        }
        
        # Step 4: Save results
        output_file = "analysis/project_analysis.md"
        save_analysis(results, output_file)