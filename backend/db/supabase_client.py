import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

# Anon client — for auth operations (signup, login)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Service role client — bypasses RLS for backend DB operations
supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
