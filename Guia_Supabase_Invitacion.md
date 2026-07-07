# 🚀 Guía: Creación de Cuenta en Supabase e Invitación de Colaboradores

Supabase es la base de datos y el backend que estamos usando para el proyecto E-Commerce. Si necesitas que otro desarrollador o compañero tenga acceso total ("Owner" / Propietario) a la base de datos, primero debe crearse una cuenta y luego debes enviarle una invitación. Sigue estos pasos:

## Fase 1: Creación de Cuenta (Para tu compañero)
Tu compañero debe realizar estos pasos antes de que lo invites:

1. Ingresar a la página oficial: [https://supabase.com/](https://supabase.com/)
2. Hacer clic en el botón verde **"Start your project"** (arriba a la derecha).
3. Registrarse usando su cuenta de **GitHub** o ingresando un **correo y contraseña**.
4. Una vez registrado, estará en el Dashboard principal de Supabase. Aún no verá ningún proyecto. ¡Es momento de que tú lo invites!

## Fase 2: Enviar la Invitación como "Owner" (Para ti)
Como tú eres el creador del proyecto actual, debes invitar a tu compañero a tu "Organización".

1. Inicia sesión en tu cuenta de [Supabase](https://supabase.com/dashboard).
2. En la página principal (Dashboard), haz clic en el ícono de **Configuración (engranaje)** en la barra lateral izquierda inferior, o ve directamente a los ajustes de tu Organización.
3. En el menú de configuración de tu Organización, busca la sección **"Team"** (Equipo) o **"Members"** (Miembros).
4. Haz clic en el botón verde **"Invite Member"** (Invitar Miembro).
5. Se abrirá una ventana. Aquí debes:
   - **Email:** Ingresar el correo con el que tu compañero acaba de registrarse en Supabase.
   - **Role:** Seleccionar **"Owner"** (Propietario). Esto le dará los mismos permisos que tienes tú (acceso a la base de datos, Storage, configuraciones y despliegues).
6. Haz clic en **"Send invite"**.

## Fase 3: Aceptar la Invitación
1. Tu compañero recibirá un correo electrónico de Supabase con el asunto de invitación.
2. Debe hacer clic en el botón **"Accept Invitation"** dentro del correo.
3. Lo redirigirá a Supabase, donde ahora podrá ver la Organización y entrar al proyecto del E-Commerce (podrá ver la base de datos de productos, órdenes, y el bucket de imágenes).

¡Listo! Con esto ambos tendrán el control total del backend del proyecto.
