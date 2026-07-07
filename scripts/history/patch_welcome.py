import os

# Patch app_cliente.py
path_cliente = 'src/app_cliente.py'
with open(path_cliente, 'r', encoding='utf-8') as f:
    c_content = f.read()

# Fix profile fetch in session restore
restore_old = """        try:
            res = supabase.auth.set_session(access_token, refresh_token)
            if res.user:
                st.session_state.user = res.user
        except Exception:"""

restore_new = """        try:
            res = supabase.auth.set_session(access_token, refresh_token)
            if res.user:
                st.session_state.user = res.user
                profile_res = supabase.table('profiles').select('*').eq('id', res.user.id).execute()
                if profile_res.data:
                    st.session_state.profile = profile_res.data[0]
        except Exception:"""
c_content = c_content.replace(restore_old, restore_new)

# Fix welcome string in app_cliente.py
welcome_old = """            name_display = st.session_state.profile['full_name'] if st.session_state.profile else st.session_state.user.email
            st.write(f"👋 Hola, **{name_display}**")"""
welcome_new = """            name_display = st.session_state.profile.get('full_name', st.session_state.user.email) if st.session_state.profile else st.session_state.user.email
            st.write(f"Hola, {name_display}")"""
c_content = c_content.replace(welcome_old, welcome_new)

# Delay before rerun to ensure cookies are set
c_content = c_content.replace('st.success(msg)\n                            st.rerun()', 'st.success(msg)\n                            import time; time.sleep(0.5)\n                            st.rerun()')
c_content = c_content.replace('st.success(msg)\n                        st.rerun()', 'st.success(msg)\n                        import time; time.sleep(0.5)\n                        st.rerun()')

with open(path_cliente, 'w', encoding='utf-8') as f:
    f.write(c_content)


# Patch app_admin.py
path_admin = 'src/app_admin.py'
with open(path_admin, 'r', encoding='utf-8') as f:
    a_content = f.read()

# Fix welcome string in app_admin.py
admin_welcome_old = """    # Sidebar
    with st.sidebar:
        st.write(f"👨‍💼 Admin: **{st.session_state.profile.get('full_name', '')}**")"""
admin_welcome_new = """    # Sidebar
    with st.sidebar:
        st.write(f"Admin: {st.session_state.profile.get('full_name', '') if st.session_state.profile else ''}")"""
a_content = a_content.replace(admin_welcome_old, admin_welcome_new)

# Delay before rerun
a_content = a_content.replace('st.success(msg)\n                    st.rerun()', 'st.success(msg)\n                    import time; time.sleep(0.5)\n                    st.rerun()')
a_content = a_content.replace('st.success(msg)\n                        st.rerun()', 'st.success(msg)\n                        import time; time.sleep(0.5)\n                        st.rerun()')


with open(path_admin, 'w', encoding='utf-8') as f:
    f.write(a_content)

print("Patch applied successfully")
