"""
🏪 PANEL DE ADMINISTRACIÓN - E-COMMERCE
Panel completo para vendedores con gestión de productos y órdenes
"""

import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime, timedelta
import json
from streamlit_cookies_controller import CookieController
import plotly.express as px
import plotly.graph_objects as go
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
from PIL import Image
import uuid

# ==================== CONFIGURACIÓN ====================

st.set_page_config(
    page_title="Panel Vendedor - E-Commerce",
    page_icon="🏪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sin estilos CSS personalizados - usamos colores nativos de Streamlit

# ==================== CONEXIÓN A SUPABASE ====================


def init_supabase() -> Client:
    """Inicializa la conexión a Supabase"""
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"❌ Error al conectar con Supabase: {str(e)}")
        st.info(
            "💡 Asegúrate de configurar tus credenciales en `.streamlit/secrets.toml`")
        st.stop()


supabase = init_supabase()


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

    st.session_state.user = None
if 'profile' not in st.session_state:
    st.session_state.profile = None



# ==================== FUNCIONES DE AUTENTICACIÓN ====================

def login_admin(email, password):
    try:
        res = supabase.auth.sign_in_with_password({"email": email, "password": password})
        # Validar rol admin
        profile_res = supabase.table('profiles').select('role, full_name').eq('id', res.user.id).execute()
        
        if profile_res.data and profile_res.data[0]['role'] == 'admin':
            st.session_state.user = res.user
            st.session_state.profile = profile_res.data[0]
            if res.session:
                controller.set('sb_admin_access', res.session.access_token)
                controller.set('sb_admin_refresh', res.session.refresh_token)
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
            if res.session:
                controller.set('sb_admin_access', res.session.access_token)
                controller.set('sb_admin_refresh', res.session.refresh_token)
            return True, "Administrador registrado exitosamente"
    except Exception as e:
        return False, str(e)

def logout_admin():
    try:
        supabase.auth.sign_out()
    except:
        pass
    controller.remove('sb_admin_access')
    controller.remove('sb_admin_refresh')
    st.session_state.user = None
    st.session_state.profile = None

# ==================== FUNCIONES DE IMÁGENES ====================

def upload_image_to_supabase(uploaded_file):
    """Sube una imagen a Supabase Storage y retorna la URL pública"""
    try:
        # Generar nombre único para el archivo
        file_extension = uploaded_file.name.split('.')[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"

        # Leer el contenido del archivo
        file_bytes = uploaded_file.read()

        # Subir a Supabase Storage
        response = supabase.storage.from_("product-images").upload(
            unique_filename,
            file_bytes,
            file_options={"content-type": uploaded_file.type}
        )

        # Obtener URL pública
        public_url = supabase.storage.from_("product-images").get_public_url(unique_filename)

        return True, public_url
    except Exception as e:
        return False, f"Error al subir imagen: {str(e)}"

def delete_image_from_supabase(image_url):
    """Elimina una imagen de Supabase Storage"""
    try:
        if not image_url:
            return True, "No hay imagen para eliminar"

        # Extraer el nombre del archivo de la URL
        filename = image_url.split('/')[-1]

        # Eliminar de Supabase Storage
        supabase.storage.from_("product-images").remove([filename])

        return True, "Imagen eliminada"
    except Exception as e:
        return False, f"Error al eliminar imagen: {str(e)}"

# ==================== FUNCIONES DE PRODUCTOS ====================


def get_all_products():
    """Obtiene todos los productos de la base de datos"""
    try:
        response = supabase.table("products").select(
            "*").order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        st.error(f"Error al obtener productos: {str(e)}")
        return []


def create_product(name, description, price, stock, category_id=None, image_url=None, variant_options=None):
    """Crea un nuevo producto en la base de datos"""
    try:
        data = {
            "name": name,
            "description": description,
            "price": float(price),
            "stock": int(stock),
            "category_id": category_id,
            "image_url": image_url
        }
        if variant_options is not None:
            data["variant_options"] = variant_options
        response = supabase.table("products").insert(data).execute()
        return True, "✅ Producto creado exitosamente"
    except Exception as e:
        return False, f"❌ Error al crear producto: {str(e)}"


def update_product(product_id, name, description, price, stock, category_id=None, image_url=None, variant_options=None):
    """Actualiza un producto existente"""
    try:
        data = {
            "name": name,
            "description": description,
            "price": float(price),
            "stock": int(stock),
            "category_id": category_id,
            "image_url": image_url
        }
        if variant_options is not None:
            data["variant_options"] = variant_options
        response = supabase.table("products").update(data).eq("id", product_id).execute()
        return True, "✅ Producto actualizado exitosamente"
    except Exception as e:
        return False, f"❌ Error al actualizar producto: {str(e)}"


def delete_product(product_id):
    """Elimina un producto"""
    try:
        response = supabase.table("products").delete().eq(
            "id", product_id).execute()
        return True, "✅ Producto eliminado exitosamente"
    except Exception as e:
        return False, f"❌ Error al eliminar producto: {str(e)}"


def get_product_by_name(name):
    """Busca un producto por nombre"""
    try:
        response = supabase.table("products").select(
            "*").eq("name", name).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        st.error(f"Error al buscar producto: {str(e)}")
        return None

# ==================== FUNCIONES DE CATEGORÍAS ====================

def get_all_categories():
    """Obtiene todas las categorías"""
    try:
        response = supabase.table("categories").select("*").order("name").execute()
        return response.data
    except Exception as e:
        st.error(f"Error al obtener categorías: {str(e)}")
        return []

def create_category(name):
    """Crea una nueva categoría"""
    try:
        response = supabase.table("categories").insert({"name": name}).execute()
        return True, "✅ Categoría creada exitosamente"
    except Exception as e:
        return False, f"❌ Error al crear categoría: {str(e)}"

def delete_category(category_id):
    """Elimina una categoría"""
    try:
        response = supabase.table("categories").delete().eq("id", category_id).execute()
        return True, "✅ Categoría eliminada exitosamente"
    except Exception as e:
        return False, f"❌ Error al eliminar categoría: {str(e)}"

# ==================== FUNCIONES DE ÓRDENES ====================


def get_all_orders():
    """Obtiene todas las órdenes"""
    try:
        response = supabase.table("orders").select(
            "*").order("created_at", desc=True).execute()
        return response.data
    except Exception as e:
        st.error(f"Error al obtener órdenes: {str(e)}")
        return []


def update_order_status(order_id, new_status, items):
    """Actualiza el estado de una orden y el stock si es necesario"""
    try:
        # Actualizar estado de la orden
        response = supabase.table("orders").update(
            {"status": new_status}).eq("id", order_id).execute()

        # Si el estado es "Completado", descontar el stock
        if new_status == "Completado":
            for item in items:
                product = get_product_by_name(item["name"])
                if product:
                    new_stock = product["stock"] - item["quantity"]
                    if new_stock < 0:
                        new_stock = 0
                    supabase.table("products").update(
                        {"stock": new_stock}).eq("id", product["id"]).execute()

        return True, f"✅ Orden marcada como {new_status}"
    except Exception as e:
        return False, f"❌ Error al actualizar orden: {str(e)}"

# ==================== FUNCIONES DE MÉTRICAS ====================


def get_dashboard_metrics():
    """Calcula las métricas del dashboard"""
    products = get_all_products()
    orders = get_all_orders()

    total_products = len(products)
    total_orders = len(orders)
    pending_orders = len([o for o in orders if o["status"] == "Pendiente"])
    total_revenue = sum([o["total_amount"]
                        for o in orders if o["status"] == "Completado"])

    return {
        "total_products": total_products,
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "total_revenue": total_revenue
    }

# ==================== FUNCIONES DE GRÁFICOS ====================

def create_sales_by_day_chart(orders):
    """Crea gráfico de ventas por día"""
    if not orders or len(orders) == 0:
        return None

    try:
        # Filtrar solo órdenes completadas para el cálculo de ventas
        completed_orders = [o for o in orders if o.get('status') == 'Completado']

        if not completed_orders:
            return None

        # Crear DataFrame
        df = pd.DataFrame(completed_orders)

        # Convertir fechas
        df['date'] = pd.to_datetime(df['created_at']).dt.date

        # Agrupar por fecha y sumar ventas
        df_grouped = df.groupby('date')['total_amount'].sum().reset_index()
        df_grouped.columns = ['Fecha', 'Ventas']

        # Ordenar por fecha
        df_grouped = df_grouped.sort_values('Fecha')

        # Crear gráfico
        fig = px.line(
            df_grouped,
            x='Fecha',
            y='Ventas',
            title=f'Ventas Diarias (Órdenes Completadas)',
            labels={'Ventas': 'Ventas (S/)', 'Fecha': 'Fecha'},
            markers=True
        )

        fig.update_traces(
            line_color='#059669',
            line_width=3,
            marker=dict(size=8)
        )

        fig.update_layout(
            hovermode='x unified',
            height=400
        )

        return fig
    except Exception as e:
        st.error(f"Error al generar gráfico de ventas: {str(e)}")
        return None

def create_orders_by_status_chart(orders):
    """Crea gráfico de órdenes por estado"""
    if not orders or len(orders) == 0:
        return None

    try:
        # Contar manualmente los estados
        status_count = {'Pendiente': 0, 'Completado': 0, 'Cancelado': 0}

        for order in orders:
            status = order.get('status', 'Desconocido')
            if status in status_count:
                status_count[status] += 1

        # Filtrar estados con 0 órdenes y convertir a lista
        states = []
        counts = []
        for estado, cantidad in status_count.items():
            if cantidad > 0:
                states.append(estado)
                counts.append(cantidad)

        if not states:
            return None

        # Colores para cada estado
        colors_list = []
        colors_map = {
            'Pendiente': '#fbbf24',
            'Completado': '#10b981',
            'Cancelado': '#ef4444'
        }

        for estado in states:
            colors_list.append(colors_map.get(estado, '#999999'))

        # Crear gráfico circular usando go.Pie directamente
        fig = go.Figure(data=[go.Pie(
            labels=states,
            values=counts,
            hole=0.3,
            marker=dict(colors=colors_list),
            textposition='auto',
            texttemplate='%{label}<br>%{value}<br>(%{percent})',
            hovertemplate='<b>%{label}</b><br>Cantidad: %{value}<br>Porcentaje: %{percent}<extra></extra>'
        )])

        fig.update_layout(
            title=f'Distribución de Órdenes por Estado (Total: {len(orders)})',
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.1
            ),
            height=400
        )

        return fig
    except Exception as e:
        st.error(f"Error al generar gráfico de estados: {str(e)}")
        return None

def create_top_products_chart(orders):
    """Crea gráfico de productos más vendidos"""
    if not orders or len(orders) == 0:
        return None

    try:
        # Solo contar productos de órdenes completadas
        completed_orders = [o for o in orders if o.get('status') == 'Completado']

        products_sold = {}
        for order in completed_orders:
            if order.get('items'):
                for item in order['items']:
                    product_name = item.get('name', 'Desconocido')
                    quantity = item.get('quantity', 0)
                    if product_name in products_sold:
                        products_sold[product_name] += quantity
                    else:
                        products_sold[product_name] = quantity

        if not products_sold:
            return None

        # Convertir a lista y ordenar
        products_list = [{'Producto': name, 'Cantidad': qty} for name, qty in products_sold.items()]
        products_list.sort(key=lambda x: x['Cantidad'], reverse=True)

        # Tomar top 10
        top_products = products_list[:10]

        if not top_products:
            return None

        df = pd.DataFrame(top_products)

        # Crear gráfico horizontal
        fig = px.bar(
            df,
            x='Cantidad',
            y='Producto',
            title='Top 10 Productos Más Vendidos',
            orientation='h',
            labels={'Cantidad': 'Cantidad Vendida', 'Producto': 'Producto'},
            text='Cantidad'
        )

        fig.update_traces(
            marker_color='#059669',
            texttemplate='%{x}',
            textposition='outside'
        )

        fig.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            height=400
        )

        return fig
    except Exception as e:
        st.error(f"Error al generar gráfico de productos: {str(e)}")
        return None

def create_revenue_by_month_chart(orders):
    """Crea gráfico de ingresos por mes"""
    if not orders or len(orders) == 0:
        return None

    try:
        # Filtrar solo órdenes completadas
        completed_orders = [o for o in orders if o.get('status') == 'Completado']

        if not completed_orders:
            return None

        # Crear DataFrame
        df = pd.DataFrame(completed_orders)

        # Convertir fechas y extraer mes
        df['date'] = pd.to_datetime(df['created_at'])
        df['month'] = df['date'].dt.to_period('M')

        # Agrupar por mes
        df_grouped = df.groupby('month')['total_amount'].sum().reset_index()
        df_grouped['month_str'] = df_grouped['month'].astype(str)
        df_grouped = df_grouped.sort_values('month')

        # Crear gráfico de barras
        fig = px.bar(
            df_grouped,
            x='month_str',
            y='total_amount',
            title='Ingresos Mensuales (Órdenes Completadas)',
            labels={'total_amount': 'Ingresos (S/)', 'month_str': 'Mes'},
            text='total_amount'
        )

        fig.update_traces(
            marker_color='#047857',
            texttemplate='S/ %{y:.2f}',
            textposition='outside'
        )

        fig.update_layout(
            height=400,
            xaxis_tickangle=-45
        )

        return fig
    except Exception as e:
        st.error(f"Error al generar gráfico de ingresos: {str(e)}")
        return None

def create_orders_trend_chart(orders):
    """Crea gráfico de tendencia de órdenes a lo largo del tiempo"""
    if not orders or len(orders) == 0:
        return None

    try:
        # Preparar datos por fecha y estado
        orders_by_date = {}
        for order in orders:
            try:
                date = pd.to_datetime(order['created_at']).date()
                status = order.get('status', 'Desconocido')

                if date not in orders_by_date:
                    orders_by_date[date] = {'Pendiente': 0, 'Completado': 0, 'Cancelado': 0}

                if status in orders_by_date[date]:
                    orders_by_date[date][status] += 1
            except:
                continue

        if not orders_by_date:
            return None

        # Convertir a lista para DataFrame
        trend_data = []
        for date, statuses in sorted(orders_by_date.items()):
            for status, count in statuses.items():
                if count > 0:  # Solo incluir si hay órdenes
                    trend_data.append({
                        'Fecha': date,
                        'Estado': status,
                        'Cantidad': count
                    })

        if not trend_data:
            return None

        df = pd.DataFrame(trend_data)

        # Colores para cada estado
        colors_map = {
            'Pendiente': '#fbbf24',
            'Completado': '#10b981',
            'Cancelado': '#ef4444'
        }

        # Crear gráfico de líneas por estado
        fig = px.line(
            df,
            x='Fecha',
            y='Cantidad',
            color='Estado',
            title='Tendencia de Órdenes por Estado',
            labels={'Cantidad': 'Número de Órdenes', 'Fecha': 'Fecha'},
            color_discrete_map=colors_map,
            markers=True
        )

        fig.update_traces(line_width=3, marker=dict(size=8))

        fig.update_layout(
            hovermode='x unified',
            height=400,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.3,
                xanchor="center",
                x=0.5
            )
        )

        return fig
    except Exception as e:
        st.error(f"Error al generar gráfico de tendencias: {str(e)}")
        return None

# ==================== FUNCIONES DE EXPORTACIÓN ====================

def generate_order_pdf(order, items):
    """Genera un PDF de una orden individual"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # Título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#059669'),
        spaceAfter=30,
        alignment=1  # Centrado
    )
    elements.append(Paragraph("ORDEN DE COMPRA", title_style))
    elements.append(Spacer(1, 0.3*inch))

    # Información de la orden
    order_info_style = styles['Normal']
    date = datetime.fromisoformat(order['created_at'].replace('Z', '+00:00'))

    elements.append(Paragraph(f"<b>Número de Orden:</b> {order['id'][:13]}", order_info_style))
    elements.append(Spacer(1, 0.1*inch))
    elements.append(Paragraph(f"<b>Fecha:</b> {date.strftime('%d/%m/%Y %H:%M')}", order_info_style))
    elements.append(Spacer(1, 0.1*inch))
    elements.append(Paragraph(f"<b>Estado:</b> {order['status']}", order_info_style))
    elements.append(Spacer(1, 0.3*inch))

    # Información del cliente
    elements.append(Paragraph("<b>DATOS DEL CLIENTE</b>", styles['Heading2']))
    elements.append(Spacer(1, 0.1*inch))
    elements.append(Paragraph(f"<b>Nombre:</b> {order['customer_name']}", order_info_style))
    elements.append(Spacer(1, 0.1*inch))
    elements.append(Paragraph(f"<b>Email:</b> {order.get('customer_email', 'No proporcionado')}", order_info_style))
    elements.append(Spacer(1, 0.1*inch))
    elements.append(Paragraph(f"<b>Teléfono:</b> {order.get('customer_phone', 'No proporcionado')}", order_info_style))
    elements.append(Spacer(1, 0.1*inch))
    elements.append(Paragraph(f"<b>Dirección:</b> {order.get('shipping_address', 'No proporcionada')}", order_info_style))
    elements.append(Spacer(1, 0.3*inch))

    # Tabla de productos
    elements.append(Paragraph("<b>PRODUCTOS</b>", styles['Heading2']))
    elements.append(Spacer(1, 0.1*inch))

    table_data = [['Producto', 'Cantidad', 'Precio Unit.', 'Subtotal']]
    for item in items:
        subtotal = item['price'] * item['quantity']
        table_data.append([
            item['name'],
            str(item['quantity']),
            f"S/ {item['price']:.2f}",
            f"S/ {subtotal:.2f}"
        ])

    table = Table(table_data, colWidths=[3*inch, 1*inch, 1.2*inch, 1.2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#059669')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(table)
    elements.append(Spacer(1, 0.3*inch))

    # Total
    total_style = ParagraphStyle(
        'Total',
        parent=styles['Normal'],
        fontSize=16,
        textColor=colors.HexColor('#059669'),
        alignment=2  # Derecha
    )
    elements.append(Paragraph(f"<b>TOTAL: S/ {order['total_amount']:.2f}</b>", total_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer

def generate_executive_summary_excel(orders, start_date, end_date):
    """Genera un resumen ejecutivo en Excel"""
    if not orders:
        return None

    df = pd.DataFrame(orders)
    df['created_at'] = pd.to_datetime(df['created_at'])

    # Aplicar filtro de fechas
    if start_date:
        df = df[df['created_at'].dt.date >= start_date]
    if end_date:
        df = df[df['created_at'].dt.date <= end_date]

    if df.empty:
        return None

    # Crear resumen
    summary_data = []
    for _, order in df.iterrows():
        items_count = len(order['items']) if order.get('items') else 0
        summary_data.append({
            'Orden ID': order['id'][:13],
            'Fecha': order['created_at'].strftime('%d/%m/%Y %H:%M'),
            'Cliente': order['customer_name'],
            'Teléfono': order.get('customer_phone', 'N/A'),
            'Estado': order['status'],
            'Items': items_count,
            'Total (S/)': f"{order['total_amount']:.2f}"
        })

    summary_df = pd.DataFrame(summary_data)

    # Guardar en buffer
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        summary_df.to_excel(writer, index=False, sheet_name='Resumen de Órdenes')

        # Agregar hoja de estadísticas
        stats_data = {
            'Métrica': [
                'Total de Órdenes',
                'Órdenes Pendientes',
                'Órdenes Completadas',
                'Órdenes Canceladas',
                'Ingresos Totales (Completadas)',
                'Ticket Promedio'
            ],
            'Valor': [
                len(df),
                len(df[df['status'] == 'Pendiente']),
                len(df[df['status'] == 'Completado']),
                len(df[df['status'] == 'Cancelado']),
                f"S/ {df[df['status'] == 'Completado']['total_amount'].sum():.2f}",
                f"S/ {df['total_amount'].mean():.2f}"
            ]
        }
        stats_df = pd.DataFrame(stats_data)
        stats_df.to_excel(writer, index=False, sheet_name='Estadísticas')

    buffer.seek(0)
    return buffer

# ==================== FUNCIONES DE UI ====================


def render_stock_badge(stock):
    """Renderiza un badge de stock con color según disponibilidad"""
    if stock > 10:
        return "🟢 Stock: " + str(stock)
    elif stock > 0:
        return "🟡 Stock: " + str(stock)
    else:
        return "🔴 Agotado"


def render_status_text(status):
    """Renderiza el texto de estado con emoji"""
    status_lower = status.lower()
    if status_lower == "pendiente":
        return f"⏳ {status}"
    elif status_lower == "completado":
        return f"✅ {status}"
    elif status_lower == "cancelado":
        return f"❌ {status}"
    return status

# ==================== PÁGINA: DASHBOARD ====================


def page_dashboard():
    """Página principal con métricas y gráficos"""
    st.title("📊 Dashboard")
    st.divider()

    # Obtener datos
    metrics = get_dashboard_metrics()
    all_orders = get_all_orders()

    # Mostrar métricas en columnas con st.metric (nativo de Streamlit)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="📦 Total Productos",
            value=metrics['total_products']
        )

    with col2:
        st.metric(
            label="🛒 Total Órdenes",
            value=metrics['total_orders']
        )

    with col3:
        st.metric(
            label="⏳ Órdenes Pendientes",
            value=metrics['pending_orders']
        )

    with col4:
        st.metric(
            label="💰 Ingresos Totales",
            value=f"S/ {metrics['total_revenue']:.2f}"
        )

    st.divider()

    # SECCIÓN DE GRÁFICOS
    if all_orders:
        st.subheader("📈 Análisis de Ventas y Órdenes")

        # Primera fila: Ventas y Estados
        col1, col2 = st.columns(2)

        with col1:
            # Gráfico de ventas por día
            chart_sales = create_sales_by_day_chart(all_orders)
            if chart_sales:
                st.plotly_chart(chart_sales, use_container_width=True)
            else:
                st.info("No hay ventas completadas para mostrar")

        with col2:
            # Gráfico de órdenes por estado
            chart_status = create_orders_by_status_chart(all_orders)
            if chart_status:
                st.plotly_chart(chart_status, use_container_width=True)
            else:
                st.info("No hay órdenes para mostrar distribución")

        # Segunda fila: Productos y Tendencias
        col1, col2 = st.columns(2)

        with col1:
            # Gráfico de productos más vendidos
            chart_products = create_top_products_chart(all_orders)
            if chart_products:
                st.plotly_chart(chart_products, use_container_width=True)
            else:
                st.info("No hay productos vendidos para mostrar")

        with col2:
            # Gráfico de tendencias de órdenes
            chart_trend = create_orders_trend_chart(all_orders)
            if chart_trend:
                st.plotly_chart(chart_trend, use_container_width=True)
            else:
                st.info("No hay datos suficientes para mostrar tendencias")

        # Tercera fila: Ingresos mensuales (ancho completo)
        st.write("")  # Espaciado
        chart_revenue = create_revenue_by_month_chart(all_orders)
        if chart_revenue:
            st.plotly_chart(chart_revenue, use_container_width=True)
        else:
            st.info("No hay ingresos mensuales para mostrar")

        st.divider()
    else:
        st.info("📊 No hay órdenes para mostrar gráficos. Las estadísticas aparecerán cuando recibas tus primeras órdenes.")

    # Órdenes recientes
    st.subheader("📋 Órdenes Recientes")
    orders = all_orders[:5] if all_orders else []  # Últimas 5 órdenes

    if orders:
        for order in orders:
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                with col1:
                    st.write(f"**{order['customer_name']}**")
                with col2:
                    st.write(render_status_text(order['status']))
                with col3:
                    st.write(f"**S/ {order['total_amount']:.2f}**")
                with col4:
                    date = datetime.fromisoformat(
                        order['created_at'].replace('Z', '+00:00'))
                    st.write(f"*{date.strftime('%d/%m/%Y %H:%M')}*")
                st.divider()
    else:
        st.info("No hay órdenes aún")

# ==================== PÁGINA: PRODUCTOS ====================


def page_products():
    """Página de gestión de productos"""
    st.title("📦 Gestión de Productos")
    st.divider()

    # Tabs para separar lista y creación
    tab1, tab2 = st.tabs(["📋 Lista de Productos", "➕ Nuevo Producto"])

    with tab1:
        products = get_all_products()

        if products:
            st.subheader(f"Total: {len(products)} productos")

            # Encabezados de la tabla simulada
            with st.container():
                hcol1, hcol2, hcol3, hcol4, hcol5, hcol6 = st.columns([1, 2, 3, 1, 1, 1])
                hcol1.markdown("**Imagen**")
                hcol2.markdown("**Nombre**")
                hcol3.markdown("**Descripción**")
                hcol4.markdown("**Precio**")
                hcol5.markdown("**Stock**")
                hcol6.markdown("**Acciones**")
            st.divider()

            for product in products:
                with st.container():
                    col1, col2, col3, col4, col5, col6 = st.columns([1, 2, 3, 1, 1, 1])

                    with col1:
                        image_url = product.get('image_url')
                        if image_url:
                            # Contenedor para imagen con tamaño fijo
                            st.markdown(f'''
                                <div style="width: 50px; height: 50px; border-radius: 5px; overflow: hidden; display: flex; justify-content: center; align-items: center; background-color: #f0f2f6;">
                                    <img src="{image_url}" style="max-width: 100%; max-height: 100%; object-fit: cover;">
                                </div>
                            ''', unsafe_allow_html=True)
                        else:
                            st.markdown("🖼️")

                    with col2:
                        st.write(f"**{product['name']}**")
                        cat_id = product.get('category_id')
                        if cat_id:
                            all_cats = get_all_categories()
                            cat_name = next((c['name'] for c in all_cats if c['id'] == cat_id), "")
                            if cat_name:
                                st.caption(cat_name)

                    with col3:
                        desc = product.get('description', '')
                        if desc and len(desc) > 50:
                            desc = desc[:50] + "..."
                        st.write(f"*{desc}*")

                    with col4:
                        st.write(f"S/ {product['price']:.2f}")

                    with col5:
                        st.write(render_stock_badge(product['stock']))

                    with col6:
                        c_edit, c_del = st.columns(2)
                        with c_edit:
                            if st.button("✏️", key=f"edit_{product['id']}", help="Editar"):
                                st.session_state.editing_product = product
                                st.rerun()
                        with c_del:
                            if st.button("🗑️", key=f"delete_{product['id']}", help="Eliminar"):
                                st.session_state.deleting_product = product
                                st.rerun()
                    st.divider()
        else:
            st.info("No hay productos registrados. ¡Crea el primero!")

    with tab2:
        st.subheader("Crear Nuevo Producto")

        categories = get_all_categories()
        
        with st.form("form_create_product"):
            new_name = st.text_input("Nombre del Producto *", placeholder="Ej: Polo Básico Blanco")
            new_desc = st.text_area("Descripción", placeholder="Describe el producto...")
            
            col1, col2 = st.columns(2)
            with col1:
                new_price = st.number_input("Precio (S/) *", min_value=0.0, step=0.5, format="%.2f")
            with col2:
                new_stock = st.number_input("Stock *", min_value=0, step=1)
            
            new_cat_name = st.selectbox("Categoría", ["Ninguna"] + [c['name'] for c in categories])
            variant_input = st.text_area("Variantes Dinámicas (Opcional)", help="FORMATO REQUERIDO:\nAtributo: valor1, valor2, valor3\n\nEjemplo:\nTalla: S, M, L\nColor: Rojo, Azul", placeholder="Talla: 40, 41, 42\nColor: Blanco, Negro")
            new_image = st.file_uploader("Imagen del Producto", type=['png', 'jpg', 'jpeg', 'webp'])
            
            submitted = st.form_submit_button("✅ Crear Producto", use_container_width=True)
            
            if submitted:
                if not new_name or new_price <= 0:
                    st.error("❌ Nombre y precio son obligatorios")
                else:
                    variant_options = []
                    if variant_input:
                        for line in variant_input.split('\n'):
                            if ':' in line:
                                attr, vals = line.split(':', 1)
                                opts = [v.strip() for v in vals.split(',') if v.strip()]
                                if attr.strip() and opts:
                                    variant_options.append({"name": attr.strip(), "values": opts})

                    image_url = None
                    if new_image:
                        success_img, result_img = upload_image_to_supabase(new_image)
                        if success_img: image_url = result_img
                            
                    cat_id = None
                    if new_cat_name != "Ninguna":
                        cat_id = next((c['id'] for c in categories if c['name'] == new_cat_name), None)
                            
                    success, msg = create_product(new_name, new_desc, new_price, new_stock, cat_id, image_url, variant_options)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

    # Modal de edición
    if 'editing_product' in st.session_state:
        product_to_edit = st.session_state.editing_product
        st.divider()
        st.subheader(f"✏️ Editar: {product_to_edit['name']}")

        with st.form("form_edit_product"):
            edit_name = st.text_input("Nombre del Producto *", value=product_to_edit['name'])
            edit_desc = st.text_area("Descripción", value=product_to_edit.get('description', ''))
            
            col1, col2 = st.columns(2)
            with col1:
                edit_price = st.number_input("Precio (S/) *", min_value=0.0, step=0.5, value=float(product_to_edit['price']), format="%.2f")
            with col2:
                edit_stock = st.number_input("Stock *", min_value=0, step=1, value=product_to_edit['stock'])

            categories = get_all_categories()
            cat_options = {c['name']: c['id'] for c in categories}
            cat_names = ["Sin categoría"] + list(cat_options.keys())
            
            # Encontrar categoría actual
            current_cat_idx = 0
            if product_to_edit.get('category_id'):
                for i, cname in enumerate(cat_names):
                    if cat_options.get(cname) == product_to_edit.get('category_id'):
                        current_cat_idx = i
                        break
            
            edit_category_name = st.selectbox("Categoría", cat_names, index=current_cat_idx)

            current_variants = product_to_edit.get('variant_options', [])
            var_str_initial = "\n".join([f"{v['name']}:{','.join(v['values'])}" for v in current_variants]) if current_variants else ""
            edit_variant_input = st.text_area("Variantes Dinámicas (Opcional)", value=var_str_initial, help="FORMATO REQUERIDO:\nAtributo: valor1, valor2, valor3\n\nEjemplo:\nTalla: S, M, L\nColor: Rojo, Azul", placeholder="Talla: 40, 41, 42\nColor: Blanco, Negro")
            edit_image = st.file_uploader("Nueva Imagen (opcional)", type=['png', 'jpg', 'jpeg', 'webp'])
            
            col_save, col_cancel = st.columns(2)
            with col_save:
                submitted = st.form_submit_button("💾 Guardar Cambios", use_container_width=True)
            with col_cancel:
                cancel = st.form_submit_button("❌ Cancelar", use_container_width=True)

            if submitted:
                if not edit_name or edit_price <= 0:
                    st.error("❌ El nombre es obligatorio y el precio debe ser mayor a 0")
                else:
                    variant_options = []
                    if edit_variant_input:
                        for line in edit_variant_input.split('\n'):
                            if ':' in line:
                                attr, vals = line.split(':', 1)
                                opts = [v.strip() for v in vals.split(',') if v.strip()]
                                if attr.strip() and opts:
                                    variant_options.append({"name": attr.strip(), "values": opts})

                    image_url_to_update = product_to_edit.get('image_url')
                    if edit_image:
                        success_img, result_img = upload_image_to_supabase(edit_image)
                        if success_img: 
                            image_url_to_update = result_img
                        else:
                            st.error(result_img)
                            st.stop()
                        
                    cat_id = cat_options.get(edit_category_name) if edit_category_name != "Sin categoría" else None
                    
                    success, msg = update_product(
                        product_to_edit['id'], edit_name, edit_desc, edit_price, edit_stock, cat_id, image_url_to_update, variant_options)
                    if success:
                        st.success(msg)
                        del st.session_state.editing_product
                        st.rerun()
                    else:
                        st.error(msg)
            
            if cancel:
                del st.session_state.editing_product
                st.rerun()

    # Modal de eliminación
    if 'deleting_product' in st.session_state:
        product = st.session_state.deleting_product

        st.divider()
        st.warning(
            f"⚠️ ¿Estás seguro de eliminar el producto **{product['name']}**?")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Sí, Eliminar", use_container_width=True, type="primary"):
                success, message = delete_product(product['id'])
                if success:
                    st.success(message)
                    del st.session_state.deleting_product
                    st.rerun()
                else:
                    st.error(message)
        with col2:
            if st.button("❌ Cancelar", use_container_width=True):
                del st.session_state.deleting_product
                st.rerun()

# ==================== PÁGINA: ÓRDENES ====================


def page_orders():
    """Página de gestión de órdenes"""
    st.title("🛒 Gestión de Órdenes")
    st.divider()

    # Filtros
    col1, col2 = st.columns([3, 1])
    with col1:
        filter_status = st.selectbox(
            "Filtrar por Estado",
            ["Todos", "Pendiente", "Completado", "Cancelado"]
        )

    # Obtener órdenes
    orders = get_all_orders()

    # Aplicar filtro
    if filter_status != "Todos":
        orders = [o for o in orders if o["status"] == filter_status]

    st.subheader(f"Total: {len(orders)} órdenes")
    st.divider()

    if orders:
        for order in orders:
            status_text = render_status_text(order['status'])
            with st.expander(f"📦 Orden #{order['id'][:8]}... - {order['customer_name']} - {status_text}", expanded=False):

                # Información del cliente
                st.subheader("👤 Datos del Cliente")
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Nombre:** {order['customer_name']}")
                    st.write(
                        f"**Email:** {order.get('customer_email', 'No proporcionado')}")
                with col2:
                    st.write(
                        f"**Teléfono:** {order.get('customer_phone', 'No proporcionado')}")
                    date = datetime.fromisoformat(
                        order['created_at'].replace('Z', '+00:00'))
                    st.write(f"**Fecha:** {date.strftime('%d/%m/%Y %H:%M')}")

                st.write(
                    f"**Dirección de Envío:** {order.get('shipping_address', 'No proporcionada')}")

                st.divider()

                # Items del pedido
                st.subheader("🛍️ Productos del Pedido")
                items = order.get('items', [])

                if items:
                    # Crear tabla de productos
                    df_items = pd.DataFrame(items)
                    df_items['subtotal'] = df_items['price'] * \
                        df_items['quantity']
                    df_items['price'] = df_items['price'].apply(
                        lambda x: f"S/ {x:.2f}")
                    df_items['subtotal'] = df_items['subtotal'].apply(
                        lambda x: f"S/ {x:.2f}")
                    df_items.columns = ['Producto',
                                        'Cantidad', 'Precio Unit.', 'Subtotal']

                    st.dataframe(
                        df_items, use_container_width=True, hide_index=True)

                    st.write(f"### **Total: S/ {order['total_amount']:.2f}**")
                else:
                    st.info("No hay items en este pedido")

                st.divider()

                # Acciones de estado
                st.subheader("🔄 Cambiar Estado")
                col1, col2, col3 = st.columns(3)

                with col1:
                    if order['status'] != "Completado":
                        if st.button("✅ Marcar como Completado", key=f"complete_{order['id']}", use_container_width=True):
                            success, message = update_order_status(
                                order['id'], "Completado", items)
                            if success:
                                st.success(message)
                                st.info(
                                    "📦 El stock de los productos ha sido actualizado")
                                st.rerun()
                            else:
                                st.error(message)

                with col2:
                    if order['status'] != "Cancelado":
                        if st.button("❌ Cancelar Orden", key=f"cancel_{order['id']}", use_container_width=True):
                            success, message = update_order_status(
                                order['id'], "Cancelado", items)
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)

                with col3:
                    if order['status'] != "Pendiente":
                        if st.button("⏳ Marcar como Pendiente", key=f"pending_{order['id']}", use_container_width=True):
                            success, message = update_order_status(
                                order['id'], "Pendiente", items)
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)

                st.write(
                    f"**Estado actual:** {render_status_text(order['status'])}")

                # Botones de exportación (solo si está completada)
                if order['status'] == "Completado":
                    st.divider()
                    st.subheader("📥 Exportar Orden")

                    col_pdf, col_excel = st.columns(2)

                    with col_pdf:
                        if st.button("📄 Generar PDF", key=f"gen_pdf_{order['id']}", use_container_width=True, type="primary"):
                            pdf_buffer = generate_order_pdf(order, items)
                            st.download_button(
                                label="⬇️ Descargar PDF",
                                data=pdf_buffer,
                                file_name=f"orden_{order['id'][:8]}.pdf",
                                mime="application/pdf",
                                key=f"download_pdf_{order['id']}",
                                use_container_width=True
                            )

                    with col_excel:
                        if st.button("📊 Generar Excel", key=f"gen_excel_{order['id']}", use_container_width=True, type="secondary"):
                            # Crear un resumen ejecutivo de solo esta orden
                            order_date = datetime.fromisoformat(order['created_at'].replace('Z', '+00:00')).date()
                            excel_buffer = generate_executive_summary_excel([order], order_date, order_date)
                            if excel_buffer:
                                st.download_button(
                                    label="⬇️ Descargar Excel",
                                    data=excel_buffer,
                                    file_name=f"orden_{order['id'][:8]}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    key=f"download_excel_{order['id']}",
                                    use_container_width=True
                                )
    else:
        st.info("No hay órdenes con el filtro seleccionado")

    # RESUMEN EJECUTIVO
    st.divider()
    st.subheader("📊 Resumen Ejecutivo")

    with st.expander("🔍 Generar Resumen de Órdenes", expanded=False):
        st.write("Filtra órdenes por rango de fechas y exporta un resumen ejecutivo en Excel")

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Fecha Inicio",
                value=datetime.now() - timedelta(days=30),
                max_value=datetime.now()
            )
        with col2:
            end_date = st.date_input(
                "Fecha Fin",
                value=datetime.now(),
                max_value=datetime.now()
            )

        if st.button("📊 Generar Resumen Ejecutivo", use_container_width=True, type="primary"):
            excel_buffer = generate_executive_summary_excel(orders, start_date, end_date)

            if excel_buffer:
                st.success("✅ Resumen generado exitosamente")
                st.download_button(
                    label="⬇️ Descargar Resumen en Excel",
                    data=excel_buffer,
                    file_name=f"resumen_ejecutivo_{start_date}_a_{end_date}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.warning("No hay órdenes en el rango de fechas seleccionado")

# ==================== PÁGINA: CATEGORÍAS ====================

def page_categories():
    """Página de gestión de categorías"""
    st.title("📑 Gestión de Categorías")
    st.divider()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Lista de Categorías")
        categories = get_all_categories()
        
        if categories:
            for cat in categories:
                with st.container():
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.write(f"**{cat['name']}**")
                    with c2:
                        if st.button("🗑️ Eliminar", key=f"del_cat_{cat['id']}"):
                            success, msg = delete_category(cat['id'])
                            if success:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                    st.divider()
        else:
            st.info("No hay categorías registradas.")
            
    with col2:
        st.subheader("Nueva Categoría")
        with st.form("form_create_category"):
            new_cat_name = st.text_input("Nombre de la Categoría *", placeholder="Ej: Ropa, Electrónica...")
            submitted = st.form_submit_button("✅ Crear", use_container_width=True)
            
            if submitted:
                if not new_cat_name:
                    st.error("❌ El nombre es obligatorio")
                else:
                    success, msg = create_category(new_cat_name.strip())
                    if success:
                        st.success(msg)
                        import time; time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(msg)

# ==================== NAVEGACIÓN ====================



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
                    import time; time.sleep(0.5)
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
                        import time; time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(msg)

def main():
    """Función principal con navegación"""
    if not st.session_state.user:
        render_admin_login()
        return

    # Sidebar
    with st.sidebar:
        st.write(f"Admin: {st.session_state.profile.get('full_name', '') if st.session_state.profile else ''}")
        if st.button("🚪 Cerrar Sesión", use_container_width=True):
            logout_admin()
            st.rerun()
            
        st.divider()

        st.title("🏪 Panel Vendedor")
        st.divider()

        page = st.radio(
            "Navegación",
            ["📊 Dashboard", "📦 Productos", "📑 Categorías", "🛒 Órdenes"],
            label_visibility="collapsed"
        )

        st.divider()
        st.subheader("ℹ️ Información")
        st.write("**Sistema E-Commerce**")
        st.write("Versión 1.0")
        st.write("Powered by Streamlit + Supabase")

    # Renderizar página seleccionada
    if page == "📊 Dashboard":
        page_dashboard()
    elif page == "📦 Productos":
        page_products()
    elif page == "📑 Categorías":
        page_categories()
    elif page == "🛒 Órdenes":
        page_orders()


if __name__ == "__main__":
    main()
