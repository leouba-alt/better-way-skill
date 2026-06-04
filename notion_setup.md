# Configuración del MCP de Notion

## Paso 1 — Crear integración en Notion
1. Ve a https://notion.so/my-integrations
2. Clic en "New integration"
3. Nombre: betterway-skill
4. Selecciona tu workspace
5. Clic en Save
6. Copia el token (empieza con secret_...)

## Paso 2 — Crear página en Notion
1. Abre Notion y crea una página nueva
2. Nómbrala "BetterWay Reports" (o el nombre que prefieras)
3. Abre los ... (tres puntos) arriba a la derecha
4. Clic en Connections → busca tu integración → conéctala

## Paso 3 — Obtener el ID de la página
1. Abre la página en el navegador
2. Copia la URL — ejemplo:
   https://app.notion.com/p/BetterWay-Reports-375fd54b327d8026918fecca6b901a12
3. El ID es la parte final: 375fd54b327d8026918fecca6b901a12

## Paso 4 — Configurar el .env
Agrega estas líneas a tu archivo .env:
   NOTION_TOKEN=secret_...
   NOTION_PARENT_PAGE_ID=375fd54b327d8026918fecca6b901a12

## Paso 5 — Verificar conexión
Ejecuta:
   python test_notion.py
Debe mostrar: Conexión exitosa. Páginas encontradas: 1