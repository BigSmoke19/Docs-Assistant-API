from ddgs import DDGS
from groq import Groq
import json
import os
from dotenv import load_dotenv
from rag import query_documents, generate_response
import re

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Define your tools
def search_documents(query: str,session_id) -> str:
    chunks,sources = query_documents(query,session_id)
    response = generate_response(query, chunks)
    return "\n".join(response),sources

available_tools = {
    "search_documents": search_documents,
}


def extract_json(text: str) -> dict:
    """Extract JSON from model response even if it has extra text around it"""
    # Try direct parse first
    try:
        return json.loads(text)
    except:
        pass
    
    # Try to find JSON pattern in the text
    try:
        match = re.search(r'\{.*?\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except:
        pass
    
    # No JSON found — treat as final answer
    return {"tool": "none", "answer": text}


def run_agent(user_question: str,session_id, silent: bool = False):
    messages = [
        {
            "role": "system",
            "content": """You are a helpful assistant that answers questions from user uploaded documents.

            RULES:
            1. ALWAYS use search_documents to find relevant information
            2. For summarization requests → use search_documents with query "main topics overview summary"
            3. Only answer based on what is found in the documents
            4. If the document does not contain the answer → say "I could not find this information in the uploaded documents"
            5. NEVER make up information or answer from your own knowledge
            6. After getting document results → give final answer immediately
            7. Keep answers concise and accurate

            Always respond in valid JSON only — no extra text, no explanation:
            {"tool": "search_documents", "input": "your search query"}

            When you have enough info to answer:
            {"tool": "none", "answer": "your final answer based on the documents", "sources"  : "Sources given by the function"}
            """

        },
        {"role": "user", "content": user_question}
    ]

    tools_used = []
    sources = []

    for iteration in range(5):
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=512
        )

        reply = response.choices[0].message.content

        parsed = extract_json(reply)

        if parsed["tool"] == "none":
            return {"answer": parsed["answer"], "tools_used": tools_used, "sources" : sources}

        tool_name = parsed["tool"]
        tool_input = parsed.get("input", "")

        # Prevent duplicate tool calls
        already_used = any(
            t["tool"] == tool_name and t["input"] == tool_input
            for t in tools_used
        )
        if already_used:
            return {
                "answer": "Could not find a definitive answer.",
                "tools_used": tools_used,
                "sources" : sources
            }

        tools_used.append({"tool": tool_name, "input": tool_input})

        if not silent:
            print(f"🔧 Using tool: {tool_name} with input: {tool_input}")

        if tool_name in available_tools:
            tool_result,sources = available_tools[tool_name](tool_input,session_id) if tool_input else available_tools[tool_name]()
        else:
            tool_result = "Tool not found"
            sources = "None"

        messages.append({"role": "assistant", "content": reply})
        messages.append({
            "role": "user",
            "content": f"Tool result: {tool_result}\n\nNow give your final answer immediately."
        })

    return {"answer": "Could not complete within allowed steps.", "tools_used": tools_used, "sources"  : sources}

def get_result(user_question: str) -> str:
    """Clean function that returns result - use this for api"""
    result = run_agent(user_question)
    return result

def get_answer(user_question: str) -> str:
    """Clean function that returns just the answer string - use this for evals"""
    result = run_agent(user_question)
    return result["answer"]

if __name__ == "__main__":

    print("""
        > Available Options:    
        - search documents(query): search internal user documents
        quit\n
        """)

    # Run it# Run it
    while True:
        question = input("You: ")
        if question.lower() == "quit":
            print("Goodbye!")
            break
        
        result = run_agent(question)
        
        print(f"\nAgent: {result['answer']}")
        
        if result['tools_used']:
            print(f"🔧 Tools used: {[t['tool'] for t in result['tools_used']]}")

        for filename in result["sources"]:
            print(f" 📄{filename}")