from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from models.request import UserQuery, ConversationRequest
from services.groq_client import call_groq_llm, stream_groq_llm
import json
from typing import List, Dict, Any

router = APIRouter()


LEGAL_MODEL = [
    {"role": "system", "content": "You are a legal expert assistant helping users with Indian law. Answer the law related questions asked by the user in an easy to understand manner. You are knowledgeable about Indian legal matters including but not limited to constitutional law, criminal law, civil law, family law, property law, and consumer protection. When providing legal information, cite relevant sections of laws or precedents when appropriate. Maintain a conversational yet professional tone."}
]

RENT_MODEL = [
    {
        "role": "system",
        "content": (
            "You are a legal assistant who drafts proper rental agreements in India based on user input. "
            "Use the following format to structure the agreement, and fill in the user-provided details. "
            "If the user misses any required info, insert the place holders so user can edit the draft accordingly keeping the format intact.\n\n"
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

async def generate_stream_with_intent(intent, llm_messages):
    """Generate a stream that first sends the intent and then the content chunks."""
    
    yield f"data: {json.dumps({'intent': intent})}\n\n"
    
    async for chunk in stream_groq_llm(llm_messages):
        if chunk:
            yield f"data: {json.dumps({'content': chunk})}\n\n"

class ConversationRequest(UserQuery):
    conversation_history: List[Dict[str, str]] = []

@router.post("/vakeel")
async def handle_user_query(payload: ConversationRequest):
    user_input = payload.user_input.strip()
    conversation_history = payload.conversation_history if hasattr(payload, 'conversation_history') else []

    try:
        # If there's existing conversation history, we're already in legal mode
        if conversation_history:
            # Create messages with conversation history
            messages = LEGAL_MODEL.copy()
            messages.extend(conversation_history)
            messages.append({"role": "user", "content": user_input})
            
            return StreamingResponse(
                generate_stream_with_intent("legal", messages),
                media_type="text/event-stream"
            )
        
        # Otherwise determine intent for new conversation
        classifier_prompt = INTENT_CLASSIFIER_PROMPT + [
            {"role": "user", "content": f"What is the intent of this query: '{user_input}'?"}
        ]
        intent_response = call_groq_llm(classifier_prompt).strip().lower()

        if "legal" in intent_response:
            messages = LEGAL_MODEL + [{"role": "user", "content": user_input}]
            return StreamingResponse(
                generate_stream_with_intent("legal", messages),
                media_type="text/event-stream"
            )

        elif "rent" in intent_response:
            messages = RENT_MODEL + [{"role": "user", "content": user_input}]
            return StreamingResponse(
                generate_stream_with_intent("rent", messages),
                media_type="text/event-stream"
            )
        
        elif "invalid" in intent_response:
            async def invalid_stream():
                yield f"data: {json.dumps({'intent': 'invalid'})}\n\n"
                yield f"data: {json.dumps({'content': 'This is not a valid task for me. Please try again.'})}\n\n"
            
            return StreamingResponse(
                invalid_stream(),
                media_type="text/event-stream"
            )

        else:
            raise ValueError(f"Unknown intent: {intent_response}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")