-- 1. Añadir columna para guardar los atributos dinámicos en los productos (JSONB)
-- Estructura esperada: [{"name": "Talla", "values": ["S", "M", "L"]}, {"name": "Color", "values": ["Rojo", "Azul"]}]
ALTER TABLE products ADD COLUMN variant_options JSONB DEFAULT '[]'::jsonb;
