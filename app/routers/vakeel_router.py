from fastapi import APIRouter, HTTPException
from models.request import UserQuery
from services.groq_client import call_groq_llm

router = APIRouter()

@router.post("/vakeel")
def handle_user_query(payload: UserQuery):
    user_input = payload.user_input.strip()

    # Step 1: Ask Groq to classify intent
    classifier_prompt = [
        {"role": "system", "content": "You are an intent classifier for a legal assistant app. Only respond with one word: 'legal' or 'rent'."},
        {"role": "user", "content": f"What is the intent of this query: '{user_input}'?"}
    ]

    try:
        intent_response = call_groq_llm(classifier_prompt).strip().lower()

        # Step 2: Forward query based on intent
        if "legal" in intent_response:
            messages = [
                {"role": "system", "content": "You are a legal expert assistant helping users with Indian law. Answer clearly and helpfully."},
                {"role": "user", "content": user_input}
            ]
            result = call_groq_llm(messages)
            return {"intent": "legal", "response": result}

        elif "rent" in intent_response:
            messages = [
                {"role": "system", "content": "You are a legal assistant who drafts proper rental agreements in India based on user input."},
                {"role": "user", "content": user_input}
            ]
            result = call_groq_llm(messages)
            return {"intent": "rent", "response": result}

        else:
            raise ValueError("Unknown intent")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
