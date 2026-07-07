# 📚 Documentación de Cambios y Nuevas Funcionalidades

Este documento registra todas las mejoras y modificaciones implementadas recientemente en el sistema E-Commerce.

## 1. Persistencia de Sesión 🔐
- **Problema Inicial:** Cada vez que el cliente o el administrador recargaban la página, la sesión se perdía, obligando a iniciar sesión nuevamente.
- **Solución Implementada:**
  - Se modificaron los archivos `src/app_cliente.py` y `src/app_admin.py` para almacenar y leer el token de sesión (`session_token`) del usuario usando almacenamiento local (o `st.query_params` / manejo avanzado de cookies en Streamlit según la implementación usada en su momento).
  - Ahora el sistema recuerda al usuario activo y lo saluda por su nombre (Ej. "Hola, [Nombre]" para el cliente y "Admin: [Nombre]" para el administrador).

## 2. Variantes Dinámicas de Productos 👕👟
- **Problema Inicial:** Los productos solo tenían atributos estáticos. Faltaba una forma de definir características como Tallas o Colores, vitales para tiendas de ropa o calzado.
- **Solución Implementada:**
  - **Base de Datos:** Se agregó la columna `variant_options` (tipo `JSONB`) a la tabla `products`, y `variant_desc` (tipo `TEXT`) a la tabla `order_items`.
  - **Panel Vendedor (`app_admin.py`):**
    - Se añadió un campo de texto para que el administrador defina las variantes de forma dinámica (ej. `Talla: S, M, L`).
    - Se implementó la lógica para analizar (parsear) el texto y guardarlo como JSON estructurado en Supabase.
  - **Tienda Cliente (`app_cliente.py`):**
    - Al abrir la tarjeta de un producto (antes de añadir al carrito), si el producto tiene variantes, se generan selectores automáticos (ej. combo box de Talla y Color).
    - La variante elegida se incluye en el carrito de compras y se guarda en el historial de la orden para que el vendedor sepa qué enviar (Ej: `Zapatillas Deportivas - Talla: 40 | Color: Negro`).

## 3. Subida y Gestión de Imágenes 🖼️
- **Problema Inicial:** Los productos no tenían una imagen asociada en la base de datos o fallaban al subir.
- **Solución Implementada:**
  - Se creó un script SQL para asegurar la creación del bucket `product-images` en Supabase Storage con políticas de acceso públicas (lectura libre, subida permitida).
  - Se integró la subida de archivos desde Streamlit hacia Supabase, obteniendo la URL pública que se guarda directamente en la tabla `products`.

## 4. Mejoras de Interfaz (UI) 💅
- **Filtros por Variantes (Cliente):** Se eliminó un panel colapsable que escondía los filtros globales. Ahora la selección de variantes se hace individualmente por cada producto en su tarjeta, logrando un diseño más limpio y directo.
- **Tabla de Productos (Admin):** Se rediseñó por completo la lista de productos en el panel del vendedor. Ahora se renderiza simulando una tabla estructurada (Imagen, Nombre, Descripción, Precio, Stock, Acciones). La imagen tiene un tamaño fijo tipo *avatar* (50x50 px con bordes redondeados) para evitar desórdenes visuales.

## 5. Scripts Automáticos (Seeders) 🚀
- Se desarrolló el script `scripts/seed_variants.py` para asignar variantes predeterminadas a los productos existentes que no tenían (como Tallas de Zapatillas, Polos, Casacas, etc.), permitiendo que el catálogo sea testeable de inmediato sin necesidad de editar todos los productos manualmente.
