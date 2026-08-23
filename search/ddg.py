import os

import requests
from ddgs import DDGS as ddg

groq_api = os.environ.get('GROQ')




def ddgSearch(chat):
    with ddg() as ddgs:
        results = ddgs.text(chat, max_results=5)
        results = f'{results}'
        return results



def groq(data, user_input):
    headers = {
        "Authorization": f"Bearer {groq_api}",
        "Content-Type": "application/json"
    }
    context = '''
You are an intelligent answer extractor
You will be given a list of search results from DuckDuckGo in the form of dictionaries with keys title href and body

Your task is to read all the results understand them and return a clear direct answer to the users query

Your response must follow these rules

1 Return only the answer no introductions no phrases like The answer is According to sources etc
2 If the query is a yes or no question always start your response with a clear Yes or No followed by a short explanation or key data if needed
For example
Q Are CBSE 10th results out
A Yes the CBSE Class 10 results are out The overall pass percentage is 93.66 percent
3 If the query is factual or definitional return only the most accurate and concise answer
For example
Q Capital of France
A Paris
4 If context is needed keep it brief and directly connected to the answer
For example
Q Who founded Microsoft
A Microsoft was founded by Bill Gates and Paul Allen in 1975
5 If information is missing ambiguous or conflicting say so briefly
For example
A The available results are unclear or contradictory about this topic
6 Ignore unrelated content ads forum spam SEO junk and repeated info

Return your final answer in a small paragraph no markdown no bullet points no citations


'''
    payload = {
        "model": "openai/gpt-oss-20b",
        "messages": [
            {"role": "system", "content": f"{context}"},
            {"role": "user", "content": f"Question: {user_input}\nSearch Results:\n{data}"}
        ],
        "max_tokens": 500
    }

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=30
    )
    response.raise_for_status()

    return response.json()["choices"][0]["message"]["content"]


# js for testing

if __name__ == "__main__":
    test_query = "Python programming"
    print(f"Testing search for: '{test_query}'\n")
    output = ddgSearch(test_query)
    inp = "python programming"
    final = groq(output, inp)
    print(final)