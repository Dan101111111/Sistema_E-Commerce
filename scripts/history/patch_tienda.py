import re
import os

with open('tienda_cliente.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add session state vars
session_state_init = """
if 'cart' not in st.session_state:
    st.session_state.cart = []
if 'order_completed' not in st.session_state:
    st.session_state.order_completed = False
if 'order_id' not in st.session_state:
    st.session_state.order_id = None
if 'order_total' not in st.session_state:
    st.session_state.order_total = 0
if 'user' not in st.session_state:
    st.session_state.user = None
if 'profile' not in st.session_state:
    st.session_state.profile = None
"""
content = re.sub(r"if 'cart' not in st.session_state:.*?st\.session_state\.order_total = 0", session_state_init.strip(), content, flags=re.DOTALL)

# 2. Add auth functions before FUNCIONES DE PRODUCTOS
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
            # Crear perfil
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

# 3. Update create_order signature
content = content.replace(
    "def create_order(customer_name, customer_email, customer_phone, shipping_address, cart_items):",
    "def create_order(customer_name, customer_email, customer_phone, shipping_address, cart_items, user_id=None):"
)
content = content.replace(
    '            "status": "Pendiente",\n            "items": items_json\n        }',
    '            "status": "Pendiente",\n            "items": items_json,\n            "user_id": user_id\n        }'
)

# 4. Update render_checkout_form to require login
checkout_replacement = """
def render_checkout_form():
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
                )

                if success:
                    st.session_state.order_completed = True
                    st.session_state.order_id = order_id
                    st.session_state.order_total = get_cart_total()
                    clear_cart()
                    st.rerun()
                else:
                    st.error(message)
"""
content = re.sub(r'def render_checkout_form\(\):.*?def render_success_message\(\):', checkout_replacement.strip() + '\n\ndef render_success_message():', content, flags=re.DOTALL)

# 5. Modify main()
main_tabs_replacement = """
    render_sidebar_auth()

    # Tabs principales
    tabs = st.tabs(["🛍️ Catálogo de Productos", "🛒 Mi Carrito", "📦 Mis Pedidos"])
    
    with tabs[0]:
"""
content = content.replace('    tab1, tab2 = st.tabs(["🛍️ Catálogo de Productos", "🛒 Mi Carrito"])\n\n    with tab1:', main_tabs_replacement)

tab2_start = content.find('    with tab2:')
if tab2_start != -1:
    content = content[:tab2_start] + content[tab2_start:].replace('    with tab2:', '    with tabs[1]:', 1)

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
content = content.replace("if __name__ == \"__main__\":", mis_pedidos_tab + "\nif __name__ == \"__main__\":")

with open('tienda_cliente.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("Patch aplicado correctamente")
