import re

with open('admin_vendedor.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add session state vars
session_state_init = """
if 'user' not in st.session_state:
    st.session_state.user = None
if 'profile' not in st.session_state:
    st.session_state.profile = None
"""
# insert right after init_supabase
content = content.replace("supabase = init_supabase()", "supabase = init_supabase()\n" + session_state_init)

# 2. Add auth functions before FUNCIONES DE SUPABASE
auth_funcs = """
# ==================== FUNCIONES DE AUTENTICACIÓN ====================

def login_admin(email, password):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        # Validar rol admin
        profile_res = supabase.table('profiles').select('role, full_name').eq('id', res.user.id).execute()
        
        if profile_res.data and profile_res.data[0]['role'] == 'admin':
            st.session_state.user = res.user
            st.session_state.profile = profile_res.data[0]
            return True, "Login exitoso"
        else:
            supabase.auth.sign_out()
            return False, "Acceso denegado: No eres administrador."
    except Exception as e:
        return False, str(e)

def register_admin(email, password, full_name, admin_secret):
    if admin_secret != "supersecreto123":
        return False, "Código secreto de administrador incorrecto."
    try:
        res = supabase.auth.sign_up({"email": email, "password": password})
        if res.user:
            supabase.table('profiles').insert({
                "id": res.user.id,
                "full_name": full_name,
                "role": "admin"
            }).execute()
            st.session_state.user = res.user
            st.session_state.profile = {"role": "admin", "full_name": full_name}
            return True, "Administrador registrado exitosamente"
    except Exception as e:
        return False, str(e)

def logout_admin():
    try:
        supabase.auth.sign_out()
    except:
        pass
    st.session_state.user = None
    st.session_state.profile = None
"""

# Insert auth functions near top, just after the first functions
first_func_marker = "# ==================== FUNCIONES DE IMÁGENES ===================="
content = content.replace(first_func_marker, auth_funcs + "\n" + first_func_marker)

# 3. Protect main
main_replacement = """
def render_admin_login():
    st.title("🔐 Panel de Administración")
    st.write("Debes iniciar sesión como administrador para acceder a este panel.")
    
    tab_login, tab_reg = st.tabs(["Ingresar", "Registrar Admin"])
    with tab_login:
        with st.form("admin_login"):
            email = st.text_input("Email")
            password = st.text_input("Contraseña", type="password")
            if st.form_submit_button("Ingresar", use_container_width=True):
                success, msg = login_admin(email, password)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)
                    
    with tab_reg:
        st.info("Para registrar un nuevo administrador, necesitas el código secreto.")
        with st.form("admin_reg"):
            reg_name = st.text_input("Nombre Completo")
            reg_email = st.text_input("Email")
            reg_pass = st.text_input("Contraseña", type="password")
            reg_secret = st.text_input("Código Secreto", type="password")
            if st.form_submit_button("Registrar Admin", use_container_width=True):
                if len(reg_pass) < 6:
                    st.error("La contraseña debe tener al menos 6 caracteres")
                else:
                    success, msg = register_admin(reg_email, reg_pass, reg_name, reg_secret)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

def main():
    \"\"\"Función principal con navegación\"\"\"
    if not st.session_state.user:
        render_admin_login()
        return

    # Sidebar
    with st.sidebar:
        st.write(f"👨‍💼 Admin: **{st.session_state.profile.get('full_name', '')}**")
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            logout_admin()
            st.rerun()
            
        st.divider()
"""
content = content.replace('def main():\n    """Función principal con navegación"""\n\n    # Sidebar\n    with st.sidebar:', main_replacement)

with open('admin_vendedor.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Patch admin_vendedor.py exitoso")
