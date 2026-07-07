import json
from supabase import create_client

def init_supabase():
    # Cargar secrets para poder instanciar
    import toml
    with open(".streamlit/secrets.toml", "r") as f:
        config = toml.load(f)
    return create_client(config["supabase"]["url"], config["supabase"]["key"])

supabase = init_supabase()
res = supabase.table("products").select("name, variant_options, image_url").eq("name", "Zapatillas Deportivas").execute()
for p in res.data:
    print(f"Product: {p['name']}")
    print(f"  Variant Options: {p['variant_options']}")
    print(f"  Image URL: {p['image_url']}")
