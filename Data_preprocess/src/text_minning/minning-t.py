import openai
import os
import re
from collections import Counter

# Step 1: Load API Key or Any other Key (maybe Llama) from the API Key file 
def load_api_key():
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("API key not found. Set it in your environment variables as 'OPENAI_API_KEY'.")
        openai.api_key = api_key
        print("API key loaded successfully.")
    except Exception as e:
        print(f"An error occurred while loading the API key: {e}")

# Step 2: Extract Contextual Information
def extract_important_details(text):
    try:
        # Use regex to extract dates, places, emails, and phone numbers
        dates = re.findall(r"\b\d{1,2}/\d{1,2}/\d{4}\b|\b\d{4}-\d{2}-\d{2}\b", text)
        emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
        phone_numbers = re.findall(r"\b\d{10,15}\b", text)
        
        # Return a dictionary of extracted data
        return {
            "dates": dates,
            "emails": emails,
            "phone_numbers": phone_numbers
        }
    except Exception as e:
        print(f"An error occurred while extracting details: {e}")
        return {}

# Step 3: Use ChatGPT to Keep Keywords and Important Context
def summarize_text_with_keywords(text):
    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=f"Extract keywords, context words, and important details (such as contacts, places, and dates) from the following text while maintaining clarity:\n{text}\n",
            max_tokens=500
        )
        summary = response["choices"][0]["text"].strip()
        return summary
    except Exception as e:
        print(f"An error occurred while using the ChatGPT API: {e}")
        return ""

# Step 4: Save the Extracted Information to a File
def save_extracted_information(extracted_data, output_file):
    try:
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w") as f:
            for key, values in extracted_data.items():
                f.write(f"{key.capitalize()}:\n")
                for value in values:
                    f.write(f"  - {value}\n")
            print(f"Extracted information saved to {output_file}.")
    except Exception as e:
        print(f"An error occurred while saving extracted information: {e}")

if __name__ == "__main__":
    input_text = """Your sample text here. Add details such as dates, contacts, and important places."""
    output_file = "data/extracted_information.txt"

    # Step 1: Load API Key
    load_api_key()

    # Step 2: Extract Contextual Information
    details = extract_important_details(input_text)

    # Step 3: Use ChatGPT for Advanced Processing
    important_summary = summarize_text_with_keywords(input_text)

    # Step 4: Save Extracted Information
    details["chatgpt_summary"] = [important_summary]  # Add summary to extracted details
    save_extracted_information(details, output_file)
