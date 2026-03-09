from fastapi import FastAPI, APIRouter, Depends, HTTPException
from pydantic import BaseModel
from supabase import create_client, Client
from dotenv import load_dotenv

import os
# Load environment variables from .env
load_dotenv()
app = FastAPI()
router = APIRouter()

# Supabase client setup
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

if not url or not key:
    raise RuntimeError("Supabase URL or Key not found in environment variables")


supabase: Client = create_client(url, key)

# -----------------------------
# Models
# -----------------------------
class WalletRequest(BaseModel):
    user_id: str

class SearchRequest(BaseModel):
    user_id: str
    origin: str
    destination_airport_id: str
    trip_type: str
    cabin: str

class RecommendRequest(BaseModel):
    user_id: str

# -----------------------------
# Wallet enforcement dependency
# -----------------------------
def enforce_wallet(user_id: str):
    result = supabase.table("wallets").select("*").eq("user_id", user_id).execute()
    if not result.data:
        raise HTTPException(status_code=403, detail="Wallet not set up")
    return result.data[0]

# -----------------------------
# Routes
# -----------------------------

@router.post("/wallet")
def get_wallet(request: WalletRequest):
    try:
        result = supabase.table("wallets").select("*").eq("user_id", request.user_id).execute()

        if not result.data:
            # Create wallet if missing
            new_wallet = {"user_id": request.user_id, "balance": 0}
            insert_result = supabase.table("wallets").insert(new_wallet).execute()
            return {"wallet": insert_result.data[0]}

        return {"wallet": result.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search")
def create_search(request: SearchRequest):
    try:
        new_search = {
            "user_id": request.user_id,
            "origin": request.origin,
            "destination_airport_id": request.destination_airport_id,
            "trip_type": request.trip_type,
            "cabin": request.cabin
        }
        result = supabase.table("searches").insert(new_search).execute()
        return {"search": result.data[0]}  # return full row with id + user_id
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommend")
def recommend(request: RecommendRequest):
    # enforce wallet existence first
    wallet = enforce_wallet(request.user_id)

    try:
        result = supabase.rpc("get_recommendations", {"uid": request.user_id}).execute()
        return {
            "wallet": wallet,
            "recommendations": result.data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/programs")
def get_programs(user_id: str):
    try:
        # Join user_programs with programs
        result = supabase.rpc("get_user_programs", {"uid": user_id}).execute()
        return {"programs": result.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


app.include_router(router)