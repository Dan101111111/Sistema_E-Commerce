-- 1. Crear tabla de categorías
CREATE TABLE categories (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Agregar la columna category_id a la tabla de productos (permite nulos temporalmente)
ALTER TABLE products ADD COLUMN category_id UUID REFERENCES categories(id) ON DELETE SET NULL;

-- 3. Insertar algunas categorías básicas de ejemplo (Opcional pero recomendado)
INSERT INTO categories (name) VALUES 
('Ropa y Accesorios'), 
('Electrónica'), 
('Hogar'), 
('Otros');
