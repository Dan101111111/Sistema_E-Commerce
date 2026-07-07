"""
🛍️ TIENDA CLIENTE - E-COMMERCE
Tienda online para que los clientes realicen sus pedidos
"""

import streamlit as st
from supabase import create_client, Client
import json
from streamlit_cookies_controller import CookieController
import re
from datetime import datetime

# ==================== CONFIGURACIÓN ====================

st.set_page_config(
    page_title="Tienda Online - E-Commerce",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS para estandarizar el tamaño de las imágenes de productos
st.markdown("""
    <style>
    /* Contenedor de imagen de producto con tamaño fijo */
    .product-image-container {
        width: 100%;
        height: 250px;
        overflow: hidden;
        display: flex;
        align-items: center;
        justify-content: center;
        background-color: #f8f9fa;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    .product-image-container img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    </style>
""", unsafe_allow_html=True)

# ==================== CONEXIÓN A SUPABASE ====================

def init_supabase() -> Client:
    """Inicializa la conexión a Supabase"""
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"❌ Error al conectar con Supabase: {str(e)}")
        st.info("💡 Asegúrate de configurar tus credenciales en `.streamlit/secrets.toml`")
        st.stop()

supabase = init_supabase()

# ==================== INICIALIZAR SESIÓN ====================


controller = CookieController()

# Intentar restaurar sesión desde cookies si no hay usuario en session_state
if 'user' not in st.session_state or not st.session_state.user:
    access_token = controller.get('sb_access_token')
    refresh_token = controller.get('sb_refresh_token')
    if access_token and refresh_token:
        try:
            res = supabase.auth.set_session(access_token, refresh_token)
            if res.user:
                st.session_state.user = res.user
                profile_res = supabase.table('profiles').select('*').eq('id', res.user.id).execute()
                if profile_res.data:
                    st.session_state.profile = profile_res.data[0]
        except Exception:
            pass

if 'cart' not in st.session_state:

    st.session_state.cart = []

if 'order_completed' not in st.session_state:
    st.session_state.order_completed = False

if 'order_id' not in st.session_state:
    st.session_state.order_id = None
if 'user' not in st.session_state:
    st.session_state.user = None
if 'profile' not in st.session_state:
    st.session_state.profile = None
if 'auth_action' not in st.session_state:
    st.session_state.auth_action = None


# ==================== FUNCIONES DE AUTENTICACIÓN ====================

def login_user(email, password):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state.user = res.user
        if res.session:
            controller.set('sb_access_token', res.session.access_token)
            controller.set('sb_refresh_token', res.session.refresh_token)
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
            if res.session:
                controller.set('sb_access_token', res.session.access_token)
                controller.set('sb_refresh_token', res.session.refresh_token)
            fetch_profile()
            return True, "Registro exitoso"
    except Exception as e:
        return False, str(e)

def logout_user():
    try:
        supabase.auth.sign_out()
    except:
        pass
    controller.remove('sb_access_token')
    controller.remove('sb_refresh_token')
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
            name_display = st.session_state.profile.get('full_name', st.session_state.user.email) if st.session_state.profile else st.session_state.user.email
            st.write(f"Hola, {name_display}")
            if st.button("🚪 Cerrar Sesión", use_container_width=True):
                logout_user()
                st.rerun()
        else:
            st.subheader("Mi Cuenta")
            
            if st.session_state.auth_action == 'login':
                st.write("🔐 **Iniciar Sesión**")
                with st.form("login_form"):
                    email = st.text_input("Email")
                    password = st.text_input("Contraseña", type="password")
                    if st.form_submit_button("Ingresar", use_container_width=True):
                        success, msg = login_user(email, password)
                        if success:
                            st.session_state.auth_action = None
                            st.success(msg)
                            import time; time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("Credenciales inválidas")
                if st.button("⬅️ Volver", use_container_width=True):
                    st.session_state.auth_action = None
                    st.rerun()
                    
            elif st.session_state.auth_action == 'register':
                st.write("📝 **Crear Cuenta**")
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
                                st.session_state.auth_action = None
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                if st.button("⬅️ Volver", use_container_width=True):
                    st.session_state.auth_action = None
                    st.rerun()
                    
            else:
                st.write("Inicia sesión o crea una cuenta para realizar tus pedidos.")
                if st.button("🔐 Iniciar Sesión", use_container_width=True, type="primary"):
                    st.session_state.auth_action = 'login'
                    st.rerun()
                if st.button("📝 Registrarse", use_container_width=True):
                    st.session_state.auth_action = 'register'
                    st.rerun()

# ==================== FUNCIONES DE PRODUCTOS ====================

def get_all_products():
    """Obtiene todos los productos disponibles"""
    try:
        response = supabase.table("products").select("*").order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        st.error(f"Error al obtener productos: {str(e)}")
        return []

def get_all_categories():
    """Obtiene todas las categorías"""
    try:
        response = supabase.table("categories").select("*").order("name").execute()
        return response.data
    except Exception as e:
        return []


# ==================== FUNCIONES DE CARRITO ====================

def add_to_cart(product, quantity, variant_desc=None):
    """Agrega un producto al carrito"""
    # Verificar si el producto ya está en el carrito
    for item in st.session_state.cart:
        if item['id'] == product['id'] and item.get('variant_desc') == variant_desc:
            item['quantity'] += quantity
            return True

    # Si no está, agregarlo
    st.session_state.cart.append({
        'id': product['id'],
        'name': product['name'],
        'price': float(product['price']),
        'quantity': quantity,
        'stock_available': product['stock'],
        'variant_desc': variant_desc
    })
    return True

def remove_from_cart(product_id, variant_desc=None):
    """Elimina un producto del carrito"""
    st.session_state.cart = [item for item in st.session_state.cart if not (item['id'] == product_id and item.get('variant_desc') == variant_desc)]

def update_cart_quantity(product_id, new_quantity, variant_desc=None):
    """Actualiza la cantidad de un producto en el carrito"""
    for item in st.session_state.cart:
        if item['id'] == product_id and item.get('variant_desc') == variant_desc:
            if new_quantity <= 0:
                remove_from_cart(product_id, variant_desc)
            else:
                item['quantity'] = new_quantity
            break

def clear_cart():
    """Vacía el carrito completamente"""
    st.session_state.cart = []

def get_cart_total():
    """Calcula el total del carrito"""
    return sum(item['price'] * item['quantity'] for item in st.session_state.cart)

def get_cart_item_count():
    """Obtiene la cantidad total de items en el carrito"""
    return sum(item['quantity'] for item in st.session_state.cart)

# ==================== FUNCIONES DE VALIDACIÓN ====================

def validate_email(email):
    """Valida el formato de un email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Valida el formato de teléfono peruano"""
    # Eliminar espacios y caracteres especiales
    phone_clean = re.sub(r'[^\d]', '', phone)
    # Debe tener al menos 9 dígitos
    return len(phone_clean) >= 9

def validate_stock_availability(cart_items):
    """Valida que todos los productos en el carrito tengan stock disponible"""
    products = get_all_products()
    products_dict = {p['id']: p for p in products}

    for item in cart_items:
        product = products_dict.get(item['id'])
        if not product:
            return False, f"El producto {item['name']} ya no está disponible"
        if product['stock'] < item['quantity']:
            return False, f"Stock insuficiente para {item['name']}. Disponible: {product['stock']}"

    return True, "Stock disponible"

# ==================== FUNCIONES DE ORDEN ====================

def create_order(customer_name, customer_email, customer_phone, shipping_address, cart_items, user_id=None):
    """Crea una nueva orden en la base de datos"""
    try:
        # Preparar items en el formato correcto
        items_json = [
            {
                "name": item['name'],
                "quantity": item['quantity'],
                "price": item['price'],
                "variant_desc": item.get('variant_desc')
            }
            for item in cart_items
        ]

        # Calcular total
        total_amount = sum(item['price'] * item['quantity'] for item in cart_items)

        # Normalizar teléfono (eliminar caracteres especiales)
        phone_clean = re.sub(r'[^\d]', '', customer_phone)

        # Crear orden
        order_data = {
            "customer_name": customer_name,
            "customer_email": customer_email,
            "customer_phone": phone_clean,
            "shipping_address": shipping_address,
            "total_amount": float(total_amount),
            "status": "Pendiente",
            "items": items_json,
            "user_id": user_id
        }

        response = supabase.table("orders").insert(order_data).execute()

        if response.data:
            return True, response.data[0]['id'], "✅ Pedido creado exitosamente"
        else:
            return False, None, "Error al crear el pedido"

    except Exception as e:
        return False, None, f"❌ Error al crear el pedido: {str(e)}"

# ==================== FUNCIONES DE UI ====================

def render_product_card(product):
    """Renderiza una card de producto usando componentes nativos de Streamlit"""

    # Determinar badge de stock
    stock = product['stock']
    if stock > 10:
        stock_text = "✓ Disponible"
        is_available = True
    elif stock > 0:
        stock_text = f"⚠️ Solo {stock} disponibles"
        is_available = True
    else:
        stock_text = "✗ Agotado"
        is_available = False

    # Descripción
    description = product.get('description', 'Sin descripción')
    if len(description) > 100:
        description = description[:100] + "..."

    # Usar container de Streamlit en lugar de HTML
    with st.container():
        # Mostrar imagen del producto con tamaño estandarizado
        image_url = product.get('image_url')
        if image_url:
            # Contenedor con altura fija para todas las imágenes usando CSS personalizado
            st.markdown(
                f"""
                <div class='product-image-container'>
                    <img src='{image_url}' alt='{product['name']}'>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            # Placeholder cuando no hay imagen con altura idéntica
            st.markdown(
                """
                <div class='product-image-container'>
                    <span style='font-size: 64px; opacity: 0.3;'>🖼️</span>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.write(f"### {product['name']}")
        
        # Mostrar categoría si existe
        cat_id = product.get('category_id')
        if cat_id:
            all_cats = get_all_categories()
            cat_name = next((c['name'] for c in all_cats if c['id'] == cat_id), "")
            if cat_name:
                st.caption(f"🏷️ {cat_name}")
                
        st.write(f"*{description}*")
        st.write(f"**S/ {product['price']:.2f}**")
        st.caption(stock_text)

        # Input de cantidad y botón
        if is_available:
            # Opciones de variantes
            variant_options = product.get('variant_options', [])
            selected_variants = {}
            if variant_options:
                for var in variant_options:
                    selected_variants[var['name']] = st.selectbox(var['name'], var['values'], key=f"var_{product['id']}_{var['name']}")

            col1, col2 = st.columns([2, 3])
            with col1:
                quantity = st.number_input(
                    "Cantidad",
                    min_value=1,
                    max_value=stock,
                    value=1,
                    key=f"qty_{product['id']}",
                    label_visibility="collapsed"
                )
            with col2:
                if st.button("🛒 Agregar", key=f"add_{product['id']}", use_container_width=True):
                    variant_desc = " | ".join([f"{k}: {v}" for k, v in selected_variants.items()]) if selected_variants else None
                    add_to_cart(product, quantity, variant_desc)
                    st.success(f"✅ {quantity}x {product['name']} agregado al carrito!")
                    st.rerun()
        else:
            st.button("❌ No Disponible", disabled=True, use_container_width=True)

def render_cart():
    """Renderiza el carrito de compras"""
    if not st.session_state.cart:
        st.info("🛒 Tu carrito está vacío. ¡Agrega productos desde el catálogo!")
        return

    st.subheader("🛍️ Productos en tu carrito")

    # Mostrar items del carrito
    for i, item in enumerate(st.session_state.cart):
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 1])

            with col1:
                st.write(f"**{item['name']}**")
                if item.get('variant_desc'):
                    st.caption(item['variant_desc'])

            with col2:
                st.write(f"S/ {item['price']:.2f}")

            with col3:
                new_qty = st.number_input(
                    "Cantidad",
                    min_value=1,
                    max_value=item['stock_available'],
                    value=item['quantity'],
                    key=f"cart_qty_{i}_{item['id']}",
                    label_visibility="collapsed"
                )
                if new_qty != item['quantity']:
                    update_cart_quantity(item['id'], new_qty, item.get('variant_desc'))
                    st.rerun()

            with col4:
                subtotal = item['price'] * item['quantity']
                st.write(f"**S/ {subtotal:.2f}**")

            with col5:
                if st.button("🗑️", key=f"remove_{i}_{item['id']}"):
                    remove_from_cart(item['id'], item.get('variant_desc'))
                    st.rerun()

            st.divider()

    # Total
    total = get_cart_total()
    st.write(f"### **Total: S/ {total:.2f}**")

    # Botones de acción
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Vaciar Carrito", use_container_width=True):
            clear_cart()
            st.rerun()

    st.divider()

    # Formulario de checkout
    render_checkout_form()

def render_checkout_form():
    """Renderiza el formulario de checkout"""
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

def render_success_message():
    """Renderiza el mensaje de éxito después de crear una orden usando componentes nativos"""
    st.balloons()

    # Mensaje de éxito principal
    st.success("### 🎉 ¡Pedido Confirmado!")
    st.write("Tu pedido ha sido registrado exitosamente")

    st.divider()

    # Información del pedido en columnas
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="📦 Número de Pedido",
            value=f"#{st.session_state.order_id[:8]}"
        )

    with col2:
        st.metric(
            label="💰 Total Pagado",
            value=f"S/ {st.session_state.order_total:.2f}"
        )

    with col3:
        st.metric(
            label="📱 Estado",
            value="Pendiente"
        )

    st.divider()

    # Información adicional
    st.info("""
    ### 📲 ¡Revisa tu WhatsApp y Email!

    Te hemos enviado:
    - 📱 **WhatsApp**: Confirmación del pedido con todos los detalles
    - 📧 **Email**: Notificación al vendedor para procesar tu orden

    El vendedor revisará tu pedido y se pondrá en contacto contigo pronto.
    """)

    if st.button("🛍️ Realizar Otro Pedido", use_container_width=True, type="primary"):
        st.session_state.order_completed = False
        st.session_state.order_id = None
        st.session_state.order_total = 0
        st.rerun()

# ==================== PÁGINA PRINCIPAL ====================

def main():
    """Función principal de la tienda"""

    # Header con componentes nativos
    st.title("🛍️ Tienda Online")
    st.write("Encuentra los mejores productos al mejor precio")

    # Indicador de carrito
    cart_count = get_cart_item_count()
    if cart_count > 0:
        st.info(f"🛒 {cart_count} {'producto' if cart_count == 1 else 'productos'} en tu carrito")

    st.divider()

    # Si se completó una orden, mostrar mensaje de éxito en la parte superior
    if st.session_state.order_completed:
        render_success_message()
        st.divider()

    # Tabs principales
    render_sidebar_auth()

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



        if products:
            # Mostrar productos en grid de 3 columnas
            cols_per_row = 3
            for i in range(0, len(products), cols_per_row):
                cols = st.columns(cols_per_row)
                for j, col in enumerate(cols):
                    if i + j < len(products):
                        with col:
                            render_product_card(products[i + j])
        else:
            st.info("No hay productos disponibles en este momento")

    with tabs[1]:
        render_cart()


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

if __name__ == "__main__":
    main()
