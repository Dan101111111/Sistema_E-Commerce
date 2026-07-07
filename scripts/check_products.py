import json
from src.app_admin import init_supabase

supabase = init_supabase()
response = supabase.table('products').select('*').execute()
for p in response.data:
    print(f"Product: {p['name']}")
    print(f"  Variant Options: {p.get('variant_options')}")
    print(f"  Image URL: {p.get('image_url')}")
