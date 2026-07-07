import re

file_path = "src/app_cliente.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update add_to_cart
old_add = """def add_to_cart(product, quantity=1):
    \"\"\"Añade un producto al carrito de compras\"\"\"
    for item in st.session_state.cart:
        if item['id'] == product['id']:
            if item['quantity'] + quantity <= product['stock']:
                item['quantity'] += quantity
                st.success(f"✅ Se actualizaron las unidades de {product['name']}")
            else:
                st.error("❌ No hay suficiente stock disponible")
            return
            
    if product['stock'] >= quantity:
        new_item = product.copy()
        new_item['quantity'] = quantity
        st.session_state.cart.append(new_item)
        st.success(f"✅ {product['name']} añadido al carrito")
    else:
        st.error("❌ No hay suficiente stock disponible")"""

new_add = """def add_to_cart(product, quantity=1, variant_desc=None):
    \"\"\"Añade un producto al carrito de compras\"\"\"
    for item in st.session_state.cart:
        if item['id'] == product['id'] and item.get('variant_desc') == variant_desc:
            if item['quantity'] + quantity <= product['stock']:
                item['quantity'] += quantity
                st.success(f"✅ Se actualizaron las unidades de {product['name']}")
            else:
                st.error("❌ No hay suficiente stock disponible")
            return
            
    if product['stock'] >= quantity:
        new_item = product.copy()
        new_item['quantity'] = quantity
        new_item['variant_desc'] = variant_desc
        st.session_state.cart.append(new_item)
        st.success(f"✅ {product['name']} añadido al carrito")
    else:
        st.error("❌ No hay suficiente stock disponible")"""
content = content.replace(old_add, new_add)

# 2. Update create_order
old_order = """        items_json = [
            {
                "name": item['name'],
                "quantity": item['quantity'],
                "price": item['price']
            }
            for item in cart_items
        ]"""
new_order = """        items_json = [
            {
                "name": item['name'],
                "quantity": item['quantity'],
                "price": item['price'],
                "variant_desc": item.get('variant_desc')
            }
            for item in cart_items
        ]"""
content = content.replace(old_order, new_order)

# 3. Update render_product_card
old_card = """        # Botones de acción
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🛒 Agregar", key=f"add_{product['id']}", disabled=not is_available, use_container_width=True):
                add_to_cart(product)"""
new_card = """        # Opciones de variantes
        variant_options = product.get('variant_options', [])
        selected_variants = {}
        if variant_options:
            for var in variant_options:
                selected_variants[var['name']] = st.selectbox(var['name'], var['values'], key=f"var_{product['id']}_{var['name']}")
                
        # Botones de acción
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🛒 Agregar", key=f"add_{product['id']}", disabled=not is_available, use_container_width=True):
                variant_desc = " | ".join([f"{k}: {v}" for k, v in selected_variants.items()]) if selected_variants else None
                add_to_cart(product, 1, variant_desc)"""
content = content.replace(old_card, new_card)

# 4. Show variant in cart UI
old_cart_ui = """                with c2:
                    st.write(f"**{item['name']}**")
                    st.write(f"S/ {item['price']:.2f} c/u")"""
new_cart_ui = """                with c2:
                    st.write(f"**{item['name']}**")
                    if item.get('variant_desc'):
                        st.caption(item['variant_desc'])
                    st.write(f"S/ {item['price']:.2f} c/u")"""
content = content.replace(old_cart_ui, new_cart_ui)

# 5. Show variant in order history UI
old_order_ui = """                                with ic2:
                                    st.write(f"**{item['name']}**")
                                    st.write(f"Cantidad: {item['quantity']}")
                                    st.write(f"Precio unitario: S/ {item['price']:.2f}")"""
new_order_ui = """                                with ic2:
                                    st.write(f"**{item['name']}**")
                                    if item.get('variant_desc'):
                                        st.caption(item['variant_desc'])
                                    st.write(f"Cantidad: {item['quantity']}")
                                    st.write(f"Precio unitario: S/ {item['price']:.2f}")"""
content = content.replace(old_order_ui, new_order_ui)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Patch cliente applied")
