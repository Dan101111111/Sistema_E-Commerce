-- 1. Crear tabla de perfiles (vinculada a los usuarios de auth)
CREATE TABLE profiles (
  id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
  full_name TEXT,
  phone TEXT,
  role TEXT DEFAULT 'client', -- Puede ser 'client' o 'admin'
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Modificar la tabla de órdenes para relacionarla con el cliente
ALTER TABLE orders ADD COLUMN user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL;
