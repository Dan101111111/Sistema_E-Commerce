-- 1. Crear el bucket 'product-images' si no existe
INSERT INTO storage.buckets (id, name, public)
VALUES ('product-images', 'product-images', true)
ON CONFLICT (id) DO NOTHING;

-- 2. Política para permitir que cualquiera pueda leer (ver las imágenes)
CREATE POLICY "Public Access to product-images"
ON storage.objects FOR SELECT
TO public
USING (bucket_id = 'product-images');

-- 3. Política para permitir que cualquiera pueda subir imágenes (insertar)
-- (En un entorno de producción estricto, podrías limitar esto a "authenticated" o a ciertos roles)
CREATE POLICY "Public Upload to product-images"
ON storage.objects FOR INSERT
TO public
WITH CHECK (bucket_id = 'product-images');

-- 4. Política para permitir que cualquiera pueda actualizar o borrar (opcional, necesario si permitimos reemplazar fotos)
CREATE POLICY "Public Update to product-images"
ON storage.objects FOR UPDATE
TO public
USING (bucket_id = 'product-images');

CREATE POLICY "Public Delete to product-images"
ON storage.objects FOR DELETE
TO public
USING (bucket_id = 'product-images');
