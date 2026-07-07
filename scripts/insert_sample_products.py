"""
Script para insertar un SEED grande de productos y órdenes de prueba en Supabase
"""

import toml
import os
import random
from datetime import datetime, timedelta
from supabase import create_client

def insert_seed_data():
    try:
        # Leer secrets del archivo TOML
        secrets_path = os.path.join(".streamlit", "secrets.toml")
        if not os.path.exists(secrets_path):
            print("❌ No se encontró el archivo .streamlit/secrets.toml")
            return

        secrets = toml.load(secrets_path)
        url = secrets["supabase"]["url"]
        key = secrets["supabase"]["key"]

        supabase = create_client(url, key)
        print("🔄 Conectando a Supabase...")

        # 1. Obtener categorias
        cats_response = supabase.table("categories").select("*").execute()
        categories = cats_response.data
        if not categories:
            print("⚠️ No se encontraron categorías. Insertando categorías por defecto...")
            default_cats = [{"name": "Ropa y Accesorios"}, {"name": "Electrónica"}, {"name": "Hogar"}, {"name": "Otros"}]
            supabase.table("categories").insert(default_cats).execute()
            cats_response = supabase.table("categories").select("*").execute()
            categories = cats_response.data

        cat_map = {c["name"]: c["id"] for c in categories}
        ropa_id = cat_map.get('Ropa y Accesorios')
        elec_id = cat_map.get('Electrónica')
        hogar_id = cat_map.get('Hogar')
        otros_id = cat_map.get('Otros')

        # 2. Insertar Productos
        print("📦 Insertando productos...")
        products = [
            {"name": "Polo Básico Blanco", "description": "100% algodón", "price": 35.0, "stock": 50, "category_id": ropa_id},
            {"name": "Jean Clásico Azul", "description": "Corte recto de mezclilla", "price": 89.9, "stock": 30, "category_id": ropa_id},
            {"name": "Smart TV 55\" 4K", "description": "Resolución Ultra HD con Smart TV", "price": 1200.0, "stock": 10, "category_id": elec_id},
            {"name": "Laptop Pro 15\"", "description": "16GB RAM, 512GB SSD, Procesador i7", "price": 2500.0, "stock": 5, "category_id": elec_id},
            {"name": "Sofá 3 Cuerpos Premium", "description": "Tela premium color gris, súper cómodo", "price": 850.0, "stock": 2, "category_id": hogar_id},
            {"name": "Lámpara de Pie Nórdica", "description": "Luz cálida LED, base de madera", "price": 120.0, "stock": 15, "category_id": hogar_id},
            {"name": "Audífonos Inalámbricos Pro", "description": "Cancelación de ruido activa, 24h de batería", "price": 199.0, "stock": 25, "category_id": elec_id},
            {"name": "Casaca de Cuero Sintético", "description": "Estilo motero, color negro", "price": 199.0, "stock": 15, "category_id": ropa_id},
            {"name": "Mochila Urbana Antirrobo", "description": "Impermeable, con puerto USB", "price": 79.9, "stock": 40, "category_id": otros_id},
            {"name": "Reloj Inteligente Fit", "description": "Monitor cardíaco, sumergible", "price": 249.0, "stock": 12, "category_id": elec_id},
            {"name": "Zapatillas Deportivas", "description": "Ideales para correr", "price": 150.0, "stock": 20, "category_id": ropa_id},
            {"name": "Set de Ollas x7", "description": "Acero inoxidable con tapa de vidrio", "price": 320.0, "stock": 8, "category_id": hogar_id},
            {"name": "Lentes de Sol Polarizados", "description": "Protección UV400", "price": 60.0, "stock": 0, "category_id": otros_id} # Stock 0 para probar
        ]
        
        for p in products:
            supabase.table("products").insert(p).execute()
        
        print(f"✅ {len(products)} productos insertados.")
        
        # 3. Insertar Órdenes (para el Dashboard)
        print("🛒 Insertando órdenes históricas para el dashboard...")
        all_prods = supabase.table("products").select("*").execute().data
        
        status_choices = ["Pendiente", "Completado", "Completado", "Completado", "Cancelado"] # Mayor peso a Completado para ver ingresos
        
        for i in range(1, 21): # 20 órdenes
            # Seleccionar 1 a 3 productos aleatorios para esta orden
            num_items = random.randint(1, 3)
            order_items = random.sample(all_prods, num_items)
            
            items_json = []
            total_amount = 0
            
            for p in order_items:
                qty = random.randint(1, 2)
                price = p['price']
                total_amount += (price * qty)
                items_json.append({"name": p["name"], "quantity": qty, "price": price})
            
            # Fecha aleatoria en los últimos 30 días
            days_ago = random.randint(0, 30)
            created = (datetime.now() - timedelta(days=days_ago)).isoformat()
            
            order = {
                "customer_name": f"Cliente de Prueba {i}",
                "customer_email": f"cliente{i}@mail.com",
                "customer_phone": f"9{random.randint(10000000, 99999999)}",
                "shipping_address": f"Av. Principal {100 + i}, Lima",
                "total_amount": total_amount,
                "status": random.choice(status_choices),
                "items": items_json,
                "created_at": created
            }
            supabase.table("orders").insert(order).execute()

        print("✅ 20 órdenes insertadas.")
        print("\n🎉 ¡SEED COMPLETO! Ya puedes ver toda la data en el dashboard.")

    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    insert_seed_data()
