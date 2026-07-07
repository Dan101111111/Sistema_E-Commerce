import json
from src.app_admin import init_supabase

def seed_variants():
    supabase = init_supabase()
    
    # Obtener todos los productos
    response = supabase.table("products").select("*").execute()
    products = response.data
    
    for p in products:
        updated = False
        current_vars = p.get('variant_options')
        
        new_variants = []
        
        # Si es el producto corrompido con el bug del \n
        if current_vars and isinstance(current_vars, list) and len(current_vars) == 1:
            if 'name' in current_vars[0] and current_vars[0]['name'] == 'Talla':
                vals = current_vars[0].get('values', [])
                if any('\n' in str(v) for v in vals):
                    # Es el producto corrompido, lo reseteamos a los valores por defecto para Zapatillas
                    new_variants = [
                        {"name": "Talla", "values": ["40", "41", "42"]},
                        {"name": "Color", "values": ["Blanco", "Negro"]}
                    ]
                    updated = True
        
        # Si no tiene variantes o están vacías (y no fue actualizado en el bloque anterior)
        if not updated and (not current_vars or len(current_vars) == 0):
            # Agregar variantes por defecto dependiendo del nombre o simplemente genericas
            if "zapatilla" in p['name'].lower():
                new_variants = [
                    {"name": "Talla", "values": ["38", "39", "40", "41", "42"]},
                    {"name": "Color", "values": ["Blanco", "Negro", "Azul"]}
                ]
            elif "polo" in p['name'].lower() or "camisa" in p['name'].lower() or "casaca" in p['name'].lower():
                new_variants = [
                    {"name": "Talla", "values": ["S", "M", "L", "XL"]},
                    {"name": "Color", "values": ["Negro", "Gris", "Blanco"]}
                ]
            else:
                new_variants = [
                    {"name": "Talla", "values": ["Única"]},
                    {"name": "Color", "values": ["Estándar"]}
                ]
            updated = True
            
        if updated:
            print(f"Actualizando '{p['name']}' con variantes: {new_variants}")
            supabase.table("products").update({"variant_options": new_variants}).eq("id", p['id']).execute()

if __name__ == "__main__":
    seed_variants()
    print("¡Semilla de variantes completada exitosamente!")
