from fastapi import FastAPI, Depends, HTTPException, status
from supabase import create_client, Client

app = FastAPI()

# --- Supabase client setup ---
url = "https://eerzllefwzswnksrlevp.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVlcnpsbGVmd3pzd25rc3JsZXZwIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3MTg5MDgzMywiZXhwIjoyMDg3NDY2ODMzfQ.AjyoSigetU8Nccals-6Vg48TegM8UgdeG3S9h2K0d78"
supabase: Client = create_client(url, key)

# --- Wallet enforcement dependency ---
def enforce_wallet_setup(user_id: str):
    result = supabase.table("users").select("wallet_completed").eq("id", user_id).execute()
    if not result.data or not result.data[0]["wallet_completed"]:
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/wallet/setup"},
            detail="Complete wallet setup before proceeding."
        )


# --- Wallet setup routes ---
@app.get("/wallet/setup")
def wallet_setup():
    return {"message": "Please complete wallet setup"}

@app.post("/wallet/complete")
def mark_wallet_complete(user_id: str):
    supabase.table("users").update({"wallet_completed": True}).eq("id", user_id).execute()
    return {"message": "Wallet setup completed"}

# --- Protected endpoints ---
@app.post("/search")
def search(params: dict, user=Depends(enforce_wallet_setup)):
    # Orchestrate search → verdict flow
    result = {"search_id": "abc123", "verdict": "Approved"}
    supabase.table("searches").insert(result).execute()
    return result

@app.get("/recommend/{search_id}")
def recommend(search_id: str, user=Depends(enforce_wallet_setup)):
    result = supabase.table("searches").select("*").eq("search_id", search_id).execute()
    if not result.data:
        return {"error": "No recommendation found"}
    return result.data[0]

@app.get("/wallet/{user_id}")
def get_wallet(user_id: str, user=Depends(enforce_wallet_setup)):
    wallet = supabase.table("wallets").select("*").eq("user_id", user_id).execute()
    return wallet.data

@app.get("/programs")
def get_programs(user=Depends(enforce_wallet_setup)):
    programs = supabase.table("programs").select("*").execute()
    return programs.data