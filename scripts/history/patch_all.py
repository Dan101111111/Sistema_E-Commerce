import os

with open('tienda_cliente.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Categories function
get_all_products_str = """def get_all_products():
    \"\"\"Obtiene todos los productos disponibles\"\"\"
    try:
        response = supabase.table("products").select("*").order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        st.error(f"Error al obtener productos: {str(e)}")
        return []"""

get_all_cats_str = """
def get_all_categories():
    \"\"\"Obtiene todas las categorías\"\"\"
    try:
        response = supabase.table("categories").select("*").order("name").execute()
        return response.data
    except Exception as e:
        return []
"""
content = content.replace(get_all_products_str, get_all_products_str + "\n" + get_all_cats_str)

# 2. Product Card category
product_card_old = """        st.write(f"### {product['name']}")
        st.write(f"*{description}*")
        st.write(f"**S/ {product['price']:.2f}**")"""

product_card_new = """        st.write(f"### {product['name']}")
        
        # Mostrar categoría si existe
        cat_id = product.get('category_id')
        if cat_id:
            all_cats = get_all_categories()
            cat_name = next((c['name'] for c in all_cats if c['id'] == cat_id), "")
            if cat_name:
                st.caption(f"🏷️ {cat_name}")
                
        st.write(f"*{description}*")
        st.write(f"**S/ {product['price']:.2f}**")"""
content = content.replace(product_card_old, product_card_new)

# 3. Session State (Fixed)
session_old = """if 'order_id' not in st.session_state:
    st.session_state.order_id = None"""

session_new = """if 'order_id' not in st.session_state:
    st.session_state.order_id = None
if 'user' not in st.session_state:
    st.session_state.user = None
if 'profile' not in st.session_state:
    st.session_state.profile = None"""
content = content.replace(session_old, session_new)

# 4. Auth Functions
auth_funcs = """
# ==================== FUNCIONES DE AUTENTICACIÓN ====================

def login_user(email, password):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state.user = res.user
        fetch_profile()
        return True, "Login exitoso"
    except Exception as e:
        return False, str(e)

def register_user(email, password, full_name, phone):
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        if res.user:
            supabase.table('profiles').insert({
                "id": res.user.id,
                "full_name": full_name,
                "phone": phone,
                "role": "client"
            }).execute()
            st.session_state.user = res.user
            fetch_profile()
            return True, "Registro exitoso"
    except Exception as e:
        return False, str(e)

def logout_user():
    try:
        supabase.auth.sign_out()
    except:
        pass
    st.session_state.user = None
    st.session_state.profile = None
    st.session_state.cart = []

def fetch_profile():
    if st.session_state.user:
        try:
            res = supabase.table('profiles').select('*').eq('id', st.session_state.user.id).execute()
            if res.data:
                st.session_state.profile = res.data[0]
        except Exception:
            pass

def get_user_orders():
    if st.session_state.user:
        try:
            res = supabase.table('orders').select('*').eq('user_id', st.session_state.user.id).order('created_at', desc=True).execute()
            return res.data
        except Exception:
            return []
    return []

def render_sidebar_auth():
    with st.sidebar:
        if st.session_state.user:
            name_display = st.session_state.profile['full_name'] if st.session_state.profile else st.session_state.user.email
            st.write(f"👋 Hola, **{name_display}**")
            if st.button("🚪 Cerrar Sesión", use_container_width=True):
                logout_user()
                st.rerun()
        else:
            st.subheader("🔐 Iniciar Sesión")
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Contraseña", type="password")
                if st.form_submit_button("Ingresar", use_container_width=True):
                    success, msg = login_user(email, password)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error("Credenciales inválidas")
            
            st.divider()
            st.subheader("📝 Crear Cuenta")
            with st.form("register_form"):
                reg_name = st.text_input("Nombre Completo")
                reg_email = st.text_input("Email")
                reg_phone = st.text_input("Teléfono")
                reg_pass = st.text_input("Contraseña", type="password")
                if st.form_submit_button("Registrarse", use_container_width=True):
                    if len(reg_pass) < 6:
                        st.error("La contraseña debe tener al menos 6 caracteres")
                    elif not reg_name or not reg_phone:
                        st.error("Llena todos los campos")
                    else:
                        success, msg = register_user(reg_email, reg_pass, reg_name, reg_phone)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
"""
content = content.replace("# ==================== FUNCIONES DE PRODUCTOS ====================", auth_funcs + "\n# ==================== FUNCIONES DE PRODUCTOS ====================")

# 5. create_order modifications
content = content.replace(
    "def create_order(customer_name, customer_email, customer_phone, shipping_address, cart_items):",
    "def create_order(customer_name, customer_email, customer_phone, shipping_address, cart_items, user_id=None):"
)
content = content.replace(
    '            "status": "Pendiente",\n            "items": items_json\n        }',
    '            "status": "Pendiente",\n            "items": items_json,\n            "user_id": user_id\n        }'
)

# 6. Checkout modifications
checkout_old = """def render_checkout_form():
    \"\"\"Renderiza el formulario de checkout\"\"\"
    st.subheader("📋 Datos de Entrega")

    with st.form("checkout_form"):
        customer_name = st.text_input(
            "Nombre Completo *",
            placeholder="Ej: Juan Pérez García"
        )

        col1, col2 = st.columns(2)
        with col1:
            customer_email = st.text_input(
                "Email *",
                placeholder="ejemplo@gmail.com"
            )
        with col2:
            customer_phone = st.text_input(
                "WhatsApp / Teléfono *",
                placeholder="921971743"
            )

        shipping_address = st.text_area(
            "Dirección de Entrega Completa *",
            placeholder="Ej: Av. Larco 123, Miraflores, Lima"
        )

        submitted = st.form_submit_button("✅ Confirmar Pedido", use_container_width=True, type="primary")

        if submitted:
            # Validaciones
            errors = []

            if not customer_name or len(customer_name.strip()) < 3:
                errors.append("❌ El nombre completo es obligatorio (mínimo 3 caracteres)")

            if not customer_email or not validate_email(customer_email):
                errors.append("❌ El email no es válido")

            if not customer_phone or not validate_phone(customer_phone):
                errors.append("❌ El teléfono debe tener al menos 9 dígitos")

            if not shipping_address or len(shipping_address.strip()) < 10:
                errors.append("❌ La dirección de entrega es obligatoria (mínimo 10 caracteres)")

            # Validar stock
            stock_valid, stock_message = validate_stock_availability(st.session_state.cart)
            if not stock_valid:
                errors.append(f"❌ {stock_message}")

            # Mostrar errores o procesar orden
            if errors:
                for error in errors:
                    st.error(error)
            else:
                # Crear orden
                success, order_id, message = create_order(
                    customer_name,
                    customer_email,
                    customer_phone,
                    shipping_address,
                    st.session_state.cart
                )"""

checkout_new = """def render_checkout_form():
    \"\"\"Renderiza el formulario de checkout\"\"\"
    st.subheader("📋 Datos de Entrega")
    
    if not st.session_state.user:
        st.warning("⚠️ Debes iniciar sesión o registrarte (en la barra lateral izquierda) para poder finalizar tu compra.")
        return

    profile = st.session_state.profile or {}

    with st.form("checkout_form"):
        customer_name = st.text_input(
            "Nombre Completo *",
            value=profile.get('full_name', ''),
            placeholder="Ej: Juan Pérez García"
        )

        col1, col2 = st.columns(2)
        with col1:
            customer_email = st.text_input(
                "Email *",
                value=st.session_state.user.email,
                placeholder="ejemplo@gmail.com",
                disabled=True
            )
        with col2:
            customer_phone = st.text_input(
                "WhatsApp / Teléfono *",
                value=profile.get('phone', ''),
                placeholder="921971743"
            )

        shipping_address = st.text_area(
            "Dirección de Entrega Completa *",
            placeholder="Ej: Av. Larco 123, Miraflores, Lima"
        )

        submitted = st.form_submit_button("✅ Confirmar Pedido", use_container_width=True, type="primary")

        if submitted:
            errors = []
            if not customer_name or len(customer_name.strip()) < 3:
                errors.append("❌ El nombre completo es obligatorio (mínimo 3 caracteres)")
            if not customer_phone or len(customer_phone.strip()) < 9:
                errors.append("❌ El teléfono debe tener al menos 9 dígitos")
            if not shipping_address or len(shipping_address.strip()) < 10:
                errors.append("❌ La dirección de entrega es obligatoria (mínimo 10 caracteres)")

            stock_valid, stock_message = validate_stock_availability(st.session_state.cart)
            if not stock_valid:
                errors.append(f"❌ {stock_message}")

            if errors:
                for error in errors:
                    st.error(error)
            else:
                success, order_id, message = create_order(
                    customer_name,
                    customer_email,
                    customer_phone,
                    shipping_address,
                    st.session_state.cart,
                    st.session_state.user.id
                )"""

content = content.replace(checkout_old, checkout_new)

# 7. Main tabs and search logic
main_old = """    tab1, tab2 = st.tabs(["🛍️ Catálogo de Productos", "🛒 Mi Carrito"])

    with tab1:
        st.subheader("Nuestros Productos")
        st.divider()

        # Obtener productos
        products = get_all_products()

        if products:"""

main_new = """    render_sidebar_auth()

    tabs = st.tabs(["🛍️ Catálogo de Productos", "🛒 Mi Carrito", "📦 Mis Pedidos"])

    with tabs[0]:
        st.subheader("Nuestros Productos")
        
        # --- BÚSQUEDA Y FILTROS ---
        col_search, col_cat = st.columns([2, 1])
        with col_search:
            search_term = st.text_input("🔍 Buscar productos...", placeholder="Escribe el nombre del producto...", label_visibility="collapsed")
        
        with col_cat:
            categories = get_all_categories()
            cat_options = ["Todas las categorías"] + [c['name'] for c in categories]
            selected_cat_name = st.selectbox("Categoría", cat_options, label_visibility="collapsed")
            
            selected_cat_id = None
            if selected_cat_name != "Todas las categorías":
                selected_cat_id = next((c['id'] for c in categories if c['name'] == selected_cat_name), None)

        st.divider()

        products = get_all_products()
        
        if search_term:
            products = [p for p in products if search_term.lower() in p['name'].lower() or (p.get('description') and search_term.lower() in p['description'].lower())]
            
        if selected_cat_id:
            products = [p for p in products if p.get('category_id') == selected_cat_id]

        if products:"""

content = content.replace(main_old, main_new)

content = content.replace("    with tab2:", "    with tabs[1]:")

mis_pedidos_tab = """
    with tabs[2]:
        st.subheader("📦 Mis Pedidos")
        if not st.session_state.user:
            st.info("Inicia sesión para ver tu historial de pedidos.")
        else:
            orders = get_user_orders()
            if not orders:
                st.info("Aún no tienes pedidos registrados.")
            else:
                for order in orders:
                    with st.expander(f"Pedido #{order['id'][:8]} - {order['created_at'][:10]} - S/ {order['total_amount']:.2f}"):
                        st.write(f"**Estado:** {order['status']}")
                        st.write(f"**Dirección:** {order.get('shipping_address', 'N/A')}")
                        st.write("**Productos:**")
                        for item in order.get('items', []):
                            st.write(f"- {item['quantity']}x {item['name']} (S/ {item['price']:.2f})")
"""
content = content.replace('if __name__ == "__main__":', mis_pedidos_tab + '\nif __name__ == "__main__":')

with open('tienda_cliente.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Patch tienda_cliente.py OK")
