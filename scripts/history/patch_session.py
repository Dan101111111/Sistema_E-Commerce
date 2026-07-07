import re

# Update requirements.txt
with open('requirements.txt', 'r', encoding='utf-8') as f:
    reqs = f.read()
if 'streamlit-cookies-controller' not in reqs:
    with open('requirements.txt', 'a', encoding='utf-8') as f:
        f.write('\nstreamlit-cookies-controller==0.0.3\n')

# Patch tienda_cliente.py
with open('tienda_cliente.py', 'r', encoding='utf-8') as f:
    t_content = f.read()

# 1. Imports
if 'from streamlit_cookies_controller import CookieController' not in t_content:
    t_content = t_content.replace('import json', 'import json\nfrom streamlit_cookies_controller import CookieController')

# 2. Remove @st.cache_resource
t_content = t_content.replace('@st.cache_resource\ndef init_supabase() -> Client:', 'def init_supabase() -> Client:')

# 3. Cookie setup and session restore
session_init = """
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
        except Exception:
            pass

if 'cart' not in st.session_state:
"""
t_content = t_content.replace("if 'cart' not in st.session_state:", session_init, 1)

# 4. Modify login_user to save cookies
login_old = """def login_user(email, password):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state.user = res.user
        fetch_profile()
        return True, "Login exitoso"
    except Exception as e:
        return False, str(e)"""
login_new = """def login_user(email, password):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        st.session_state.user = res.user
        if res.session:
            controller.set('sb_access_token', res.session.access_token)
            controller.set('sb_refresh_token', res.session.refresh_token)
        fetch_profile()
        return True, "Login exitoso"
    except Exception as e:
        return False, str(e)"""
t_content = t_content.replace(login_old, login_new)

# 5. Modify register_user to save cookies
reg_old = """        if res.user:
            supabase.table('profiles').insert({
                "id": res.user.id,
                "full_name": full_name,
                "phone": phone,
                "role": "client"
            }).execute()
            st.session_state.user = res.user
            fetch_profile()
            return True, "Registro exitoso\""""
reg_new = """        if res.user:
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
            return True, "Registro exitoso\""""
t_content = t_content.replace(reg_old, reg_new)

# 6. Modify logout_user
logout_old = """def logout_user():
    try:
        supabase.auth.sign_out()
    except:
        pass
    st.session_state.user = None
    st.session_state.profile = None
    st.session_state.cart = []"""
logout_new = """def logout_user():
    try:
        supabase.auth.sign_out()
    except:
        pass
    controller.remove('sb_access_token')
    controller.remove('sb_refresh_token')
    st.session_state.user = None
    st.session_state.profile = None
    st.session_state.cart = []"""
t_content = t_content.replace(logout_old, logout_new)

with open('tienda_cliente.py', 'w', encoding='utf-8') as f:
    f.write(t_content)


# Patch admin_vendedor.py
with open('admin_vendedor.py', 'r', encoding='utf-8') as f:
    a_content = f.read()

# 1. Imports
if 'from streamlit_cookies_controller import CookieController' not in a_content:
    a_content = a_content.replace('import json', 'import json\nfrom streamlit_cookies_controller import CookieController')

# 2. Remove @st.cache_resource
a_content = a_content.replace('@st.cache_resource\ndef init_supabase() -> Client:', 'def init_supabase() -> Client:')

# 3. Cookie setup and session restore
session_init_admin = """
controller = CookieController()

# Intentar restaurar sesión desde cookies
if 'user' not in st.session_state or not st.session_state.user:
    access_token = controller.get('sb_admin_access')
    refresh_token = controller.get('sb_admin_refresh')
    if access_token and refresh_token:
        try:
            res = supabase.auth.set_session(access_token, refresh_token)
            if res.user:
                profile_res = supabase.table('profiles').select('role, full_name').eq('id', res.user.id).execute()
                if profile_res.data and profile_res.data[0]['role'] == 'admin':
                    st.session_state.user = res.user
                    st.session_state.profile = profile_res.data[0]
        except Exception:
            pass

if 'user' not in st.session_state:
"""
a_content = a_content.replace("if 'user' not in st.session_state:", session_init_admin, 1)

# 4. Modify login_admin to save cookies
login_admin_old = """        if profile_res.data and profile_res.data[0]['role'] == 'admin':
            st.session_state.user = res.user
            st.session_state.profile = profile_res.data[0]
            return True, "Login exitoso\""""
login_admin_new = """        if profile_res.data and profile_res.data[0]['role'] == 'admin':
            st.session_state.user = res.user
            st.session_state.profile = profile_res.data[0]
            if res.session:
                controller.set('sb_admin_access', res.session.access_token)
                controller.set('sb_admin_refresh', res.session.refresh_token)
            return True, "Login exitoso\""""
a_content = a_content.replace(login_admin_old, login_admin_new)

# 5. Modify register_admin to save cookies
reg_admin_old = """            st.session_state.user = res.user
            st.session_state.profile = {"role": "admin", "full_name": full_name}
            return True, "Administrador registrado exitosamente\""""
reg_admin_new = """            st.session_state.user = res.user
            st.session_state.profile = {"role": "admin", "full_name": full_name}
            if res.session:
                controller.set('sb_admin_access', res.session.access_token)
                controller.set('sb_admin_refresh', res.session.refresh_token)
            return True, "Administrador registrado exitosamente\""""
a_content = a_content.replace(reg_admin_old, reg_admin_new)

# 6. Modify logout_admin
logout_admin_old = """def logout_admin():
    try:
        supabase.auth.sign_out()
    except:
        pass
    st.session_state.user = None
    st.session_state.profile = None"""
logout_admin_new = """def logout_admin():
    try:
        supabase.auth.sign_out()
    except:
        pass
    controller.remove('sb_admin_access')
    controller.remove('sb_admin_refresh')
    st.session_state.user = None
    st.session_state.profile = None"""
a_content = a_content.replace(logout_admin_old, logout_admin_new)

with open('admin_vendedor.py', 'w', encoding='utf-8') as f:
    f.write(a_content)

print("Patch session cookies OK")
