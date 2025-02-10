import requests


url = "https://api-inference.huggingface.co/models/deepseek-ai/DeepSeek-R1-Distill-Qwen-14B"
token = "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"



def llm(query):
    parameters = {
        "max_new_tokens": 5000,
        "temperature": 0.01,
        "top_k": 50,
        "top_p": 0.95,
        "return_full_text": True
    }

    prompt = """<|begin_of_text|><|start_header_id|>system<|end_header_id|>You are a helpful and smart assistant. You accurately provide an answer to the provided user query.<|eot_id|><|start_header_id|>user<|end_header_id|> Here is the query: ```{query}```.
    Provide a precise and concise answer.<|eot_id|><|start_header_id|>assistant<|end_header_id|>"""

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    prompt = prompt.replace("{query}", query)

    payload = {
        "inputs": prompt,
        "parameters": parameters
    }

    response = requests.post(url, headers=headers, json=payload)

    try:
        response_text = response.json()[0]['generated_text'].strip()
        return response_text
    except (KeyError, IndexError):
        return "Error: Unable to retrieve a valid response."

if __name__ == "__main__":
    user_input = input("Posé votre question please :) : ")  # Prompt the user for input
    print("\nEntrain de réflechir 2s stp ;) ..... \n")
    result = llm(user_input)  # Pass the user input to the function
    print(result)
