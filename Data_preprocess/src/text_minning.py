import requests
import pandas as pd
from collections import Counter
from tkinter import Tk, filedialog
import re

# Function to select the API key's 
def select_api_key_file():
    Tk().withdraw()
    file_path = filedialog.askopenfilename(title="Select API Key File")
    try:
        with open(file_path, "r") as file:
            return file.read().strip()
    except:
        print("Error loading API key file")
        return None

def extract_text_features(text):

    ####  A modfié par les BA, ajouté des patterns necessaire #####

    # Define the pattterns
    patterns = {
        "dates": r"\b(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4})\b",
        "emails": r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b",
        "phone_numbers": r"\b(?:\+?(\d{1,3})[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
        "urls": r"\bhttps?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+\b"
    }
    
    extracted = {}
    for key, pattern in patterns.items():
        extracted[key] = list(set(re.findall(pattern, text, flags=re.IGNORECASE)))
    
    # Get word frequencies
    words = re.findall(r'\b\w{4,}\b', text.lower())
    extracted["frequent_words"] = Counter(words).most_common(10)
    
    return extracted

def analyze_with_llm(text, api_key):
    url = "https://api-inference.huggingface.co/models/meta-llama/Meta-Llama-3-8B-Instruct"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    prompt = """Analyze the following text and provide:
    1. Main topics discussed
    2. Key insights
    3. Important entities mentioned
    4. Overall sentiment
    Text: ```{text}```"""
    
    payload = {
        "inputs": prompt.replace("{text}", text),
        "parameters": {
            "max_new_tokens": 500,
            "temperature": 0.01,
            "top_k": 50,
            "top_p": 0.95
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        return response.json()[0]['generated_text'].strip()
    except:
        return "Error in AI analysis"

def save_results(extracted_data, ai_analysis, output_file="text_mining_results.xlsx"):
    # Create separate dataframes for each type of data
    dfs = {}
    
    # Word frequencies
    word_freq_df = pd.DataFrame(extracted_data["frequent_words"], 
                              columns=["Word", "Frequency"])
    dfs["Word_Frequencies"] = word_freq_df
    
    # Other extracted features
    for key in ["dates", "emails", "phone_numbers", "urls"]:
        if extracted_data[key]:
            dfs[key.title()] = pd.DataFrame(extracted_data[key], 
                                          columns=[key.title()])
    
    # AI Analysis
    ai_analysis_df = pd.DataFrame({"AI Analysis": [ai_analysis]})
    dfs["AI_Analysis"] = ai_analysis_df
    
    # Save to Excel with multiple sheets
    with pd.ExcelWriter(output_file) as writer:
        for sheet_name, df in dfs.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    return output_file

def main():
    # Get API key
    api_key = select_api_key_file()
    if not api_key:
        return
    
    # Get input text
    text = input("Enter the text to analyze: ")
    print("\nAnalyzing text...")
    
    # Extract features and analyze
    extracted_data = extract_text_features(text)
    ai_analysis = analyze_with_llm(text, api_key)
    
    # Save results
    output_file = save_results(extracted_data, ai_analysis)
    print(f"\nResults saved to {output_file}")

if __name__ == "__main__":
    main()