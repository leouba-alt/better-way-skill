# BetterWay Skill — Priorización Agéntica de Candidatos

## ¿Qué hace este skill?
Toma descripciones de puestos y perfiles de candidatos en PDF, clasifica cada candidato
(Puesto A / Puesto B / Ambos / Ninguno), asigna un score de relevancia, y publica
un reporte priorizado en Notion vía la API oficial.

## Requisitos
- Python 3.10+
- Cuenta de Anthropic con API key
- Cuenta de Notion con una integración creada

## Instalación
1. Clona el repositorio
2. Crea y activa el entorno virtual:
   python -m venv venv
   venv\Scripts\activate        # Windows
   source venv/bin/activate     # Mac/Linux
3. Instala dependencias:
   pip install -r requirements.txt

## Configuración
Crea un archivo .env en la raíz con:
   ANTHROPIC_API_KEY=sk-ant-...
   NOTION_TOKEN=secret_...
   NOTION_PARENT_PAGE_ID=id-de-tu-pagina-notion

## Estructura de inputs
Coloca los archivos en la carpeta inputs/:
   inputs/
   ├── job-a-[nombre-puesto].pdf
   ├── job-b-[nombre-puesto].pdf
   └── candidates/
       ├── candidate-01.pdf
       ├── candidate-02.pdf
       └── ...

## Ejecución
   python skill.py

## Output
El skill publica automáticamente un reporte en Notion con:
- Candidatos priorizados por puesto (ordenados por score)
- Fortalezas y riesgos por candidato
- Sección de candidatos que aplican a ambos puestos
- Lista de descartados con razón