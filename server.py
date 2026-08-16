# src/server.py
from fastapi import FastAPI, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import logging
import json

app = FastAPI(title="Kapture VoiceBot API", description="Endpoints for Vapi tool integration")

# ============================================================
# CORS
# ============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# LOGGING
# ============================================================
logging.basicConfig(level=logging.INFO)

# ============================================================
# DATA MODELS (for Swagger docs)
# ============================================================
class VerifyCustomerBody(BaseModel):
    customer_id: str | None = None
    dob: str | None = None
    pan_last4: str | None = None

class PromiseToPayBody(BaseModel):
    customer_id: str | None = None
    amount: float | None = None
    date: str | None = None

class PaymentLinkBody(BaseModel):
    customer_id: str | None = None
    link: str | None = None

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def extract_vapi_tool_data(body: dict):
    """Extract toolCallId and arguments from Vapi's request."""
    message = body.get("message", {})
    tool_call_list = message.get("toolCallList", [])
    if not tool_call_list:
        return None, {}
    tool_call = tool_call_list[0]
    tool_call_id = tool_call.get("id")
    function = tool_call.get("function", {})
    arguments = function.get("arguments", {})
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except json.JSONDecodeError:
            logging.error(f"Could not parse arguments: {arguments}")
            arguments = {}
    return tool_call_id, arguments

def vapi_response(tool_call_id: str | None, result: str):
    """Return the response format expected by Vapi."""
    return {"results": [{"toolCallId": tool_call_id, "result": result}]}

# ============================================================
# ROOT
# ============================================================
@app.get("/")
def read_root():
    return {"message": "FastAPI server is running!"}

# ============================================================
# VERIFY CUSTOMER
# ============================================================
@app.post("/verify_customer", response_model=dict)
async def verify_customer(body: VerifyCustomerBody, request: Request):
    try:
        raw_body = await request.json()
    except Exception:
        raw_body = {}
    logging.info(f"Incoming /verify_customer body: {raw_body}")

    tool_call_id, arguments = extract_vapi_tool_data(raw_body)
    customer_id = body.customer_id or arguments.get("customer_id")
    dob = body.dob or arguments.get("dob")
    pan_last4 = body.pan_last4 or arguments.get("pan_last4")

    verified = bool(dob and pan_last4)
    result = (
        "Customer verification successful. The customer's identity has been verified."
        if verified
        else "Customer verification failed. The required date of birth and PAN details were not provided."
    )
    response = vapi_response(tool_call_id, result)
    logging.info(f"/verify_customer response: {response}")
    return response

# ============================================================
# LOG PROMISE TO PAY
# ============================================================
@app.post("/log_promise_to_pay", response_model=dict)
async def log_promise_to_pay(body: PromiseToPayBody, request: Request):
    try:
        raw_body = await request.json()
    except Exception:
        raw_body = {}
    logging.info(f"Incoming /log_promise_to_pay body: {raw_body}")

    tool_call_id, arguments = extract_vapi_tool_data(raw_body)
    customer_id = body.customer_id or arguments.get("customer_id")
    amount = body.amount or arguments.get("amount")
    date = body.date or arguments.get("date")

    if customer_id and amount is not None and date:
        result = f"Promise to pay recorded successfully. Customer ID: {customer_id}. Amount: {amount}. Payment date: {date}."
    else:
        result = "Promise to pay could not be recorded because required information is missing."

    response = vapi_response(tool_call_id, result)
    logging.info(f"/log_promise_to_pay response: {response}")
    return response

# ============================================================
# SEND PAYMENT LINK
# ============================================================
@app.post("/send_payment_link", response_model=dict)
async def send_payment_link(body: PaymentLinkBody, request: Request):
    try:
        raw_body = await request.json()
    except Exception:
        raw_body = {}
    logging.info(f"Incoming /send_payment_link body: {raw_body}")

    tool_call_id, arguments = extract_vapi_tool_data(raw_body)
    customer_id = body.customer_id or arguments.get("customer_id")
    link = body.link or arguments.get("link")

    if customer_id and link:
        result = f"Payment link sent successfully to customer {customer_id}."
    else:
        result = "Payment link could not be sent because customer ID or payment link is missing."

    response = vapi_response(tool_call_id, result)
    logging.info(f"/send_payment_link response: {response}")
    return response
