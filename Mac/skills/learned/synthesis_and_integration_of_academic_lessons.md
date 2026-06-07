# synthesis_and_integration_of_academic_lessons

## Descripcion
Sintetizar lecciones universitarias estructuradas con LaTeX y MathJax a partir de transcripciones vectorizadas de Qdrant e integrarlas secuencialmente en el panel web.

## Trigger
Usar este skill cuando: Cuando se necesite crear un plan de estudios o lecciones a partir de múltiples vídeos indexados y mostrarlas interactivamente en la interfaz de usuario.

## Pasos
- Paso 1: Recuperar fragmentos vectoriales de Qdrant asociados a temas académicos.
- Paso 2: Compilar un mapa de conceptos canónicos unificados para estructurar el plan de estudios.
- Paso 3: Alimentar en lotes a un modelo matemático local o gratuito (como qwen2-math) para redactar lecciones detalladas en LaTeX.
- Paso 4: Convertir las ecuaciones y formato a HTML premium compatible con MathJax v3, saneando secuencias de escape JSON y barras invertidas.
- Paso 5: Indexar las lecciones sintetizadas en una colección dedicada de Qdrant ordenada canónicamente por ID.
- Paso 6: Modificar el endpoint de búsqueda backend del panel web para recuperar y ordenar las lecciones de la base de datos.
- Paso 7: Actualizar el frontend de la Charm Edu para cargar las lecciones y llamar a MathJax.typesetPromise() al renderizar.

## Herramientas necesarias
python, qdrant, qwen2-math, MathJax

## Constraints
- Mantener rigor científico y ecuaciones centradas.
- Sanear escapes en el intercambio JSON backend/frontend.
- Asegurar orden numérico ascendente por id.

## Ejemplo de uso
```
python generate_comprehensive_curriculum.py
```

## Metadata
- Generado: 2026-05-20T00:11:32.864832
- Fuente: Aprendizaje autónomo (Enjambre Hive Mind)
- Validado: auto-generated
- Version: 1.0
