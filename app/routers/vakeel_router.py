from fastapi import APIRouter, HTTPException
from models.request import UserQuery
from services.groq_client import call_groq_llm

router = APIRouter()


LEGAL_MODEL = [
    {"role": "system", "content": "You are a legal expert assistant helping users with Indian law. Answer the law related questions asked by the user in an easy to understand manner."}
]

RENT_MODEL = [
    {
        "role": "system",
        "content": (
            "You are a legal assistant who drafts proper rental agreements in India based on user input. "
            "Use the following format to structure the agreement, and fill in the user-provided details. "
            "If the user misses any required info, make best assumptions but keep the format intact.\n\n"
            "---- SAMPLE RENT AGREEMENT FORMAT ----\n"
            "This Rent Agreement is made on [Date] between:\n\n"
            "1. Landlord: [Landlord Name], residing at [Landlord Address]\n"
            "2. Tenant: [Tenant Name], residing at [Tenant Address]\n\n"
            "The Landlord agrees to let and the Tenant agrees to take the property located at [Rented Property Address] on the following terms:\n\n"
            "1. Monthly Rent: ₹[Amount]\n"
            "2. Security Deposit: ₹[Deposit]\n"
            "3. Duration: [Duration] months starting from [Start Date]\n"
            "4. Electricity and Water Bills: To be paid by the Tenant\n"
            "5. Maintenance Charges: [To be paid by Tenant/Landlord]\n"
            "6. Notice Period: [Notice Period] for termination by either party\n\n"
            "This agreement is signed on [Date] by both parties.\n\n"
            "Landlord Signature: ___________\n"
            "Tenant Signature: ___________"
        )
    }
]


INTENT_CLASSIFIER_PROMPT = [
    {"role": "system", "content": "You are an intent classifier for a legal assistant app. Only respond with one word: 'legal' or 'rent'. Provide 'invalid' as intent if it matches with none of the intent of legal or rent"}
]

@router.post("/vakeel")
def handle_user_query(payload: UserQuery):
    user_input = payload.user_input.strip()

    try:
        
        classifier_prompt = INTENT_CLASSIFIER_PROMPT + [
            {"role": "user", "content": f"What is the intent of this query: '{user_input}'?"}
        ]
        intent_response = call_groq_llm(classifier_prompt).strip().lower()

        if "legal" in intent_response:
            messages = LEGAL_MODEL + [{"role": "user", "content": user_input}]
            result = call_groq_llm(messages)
            return {"intent": "legal", "response": result}

        elif "rent" in intent_response:
            messages = RENT_MODEL + [{"role": "user", "content": user_input}]
            result = call_groq_llm(messages)
            return {"intent": "rent", "response": result}
        
        elif "invalid" in intent_response:
            return {"intent" : "invalid", "response": "This is not a valid task for me. Please try again."}

        else:
            raise ValueError(f"Unknown intent: {intent_response}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
