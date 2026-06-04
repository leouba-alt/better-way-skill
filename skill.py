import os
import glob
import json
import re
from pathlib import Path
import fitz
import anthropic
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
notion = Client(auth=os.getenv("NOTION_TOKEN"))

def read_pdf(path: str) -> str:
    doc = fitz.open(path)
    return "\n".join(page.get_text() for page in doc)

def classify_candidate(candidate_text: str, job_a: str, job_b: str) -> dict:
    prompt = f"""Eres un experto en reclutamiento técnico. Analiza el perfil del candidato y decide si encaja con el Puesto A, Puesto B, ambos o ninguno.

## PUESTO A — Integration Developer Oracle EBS
{job_a}

## PUESTO B — Business Systems Analyst Oracle EBS
{job_b}

## PERFIL DEL CANDIDATO
{candidate_text}

Responde ÚNICAMENTE con un JSON válido con esta estructura exacta:
{{
  "nombre": "nombre completo del candidato",
  "puesto_a": true,
  "puesto_b": false,
  "score_a": 7,
  "score_b": 3,
  "fortalezas": "máximo 2 líneas con las fortalezas clave",
  "riesgos": "máximo 1 línea con riesgos o gaps importantes, o Ninguno",
  "recomendacion": "A"
}}

Los valores de puesto_a y puesto_b deben ser true o false (sin comillas).
Los scores deben ser números enteros del 0 al 10.
recomendacion debe ser exactamente una de estas opciones: A, B, Ambos, Ninguno.
No agregues texto antes ni después del JSON. No uses comillas en los booleanos."""

    response = anthropic_client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response.content[0].text.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                pass
        return {
            "nombre": Path("unknown").stem,
            "puesto_a": False, "puesto_b": False,
            "score_a": 0, "score_b": 0,
            "fortalezas": "No se pudo procesar el perfil",
            "riesgos": "Error en clasificación",
            "recomendacion": "Ninguno"
        }

def process_candidates(inputs_dir: str) -> list:
    job_a = read_pdf(f"{inputs_dir}/job-a-integration-developer-oracle-ebs.pdf")
    job_b = read_pdf(f"{inputs_dir}/job-b-business-systems-analyst-oracle-ebs.pdf")

    pdf_files = sorted(glob.glob(f"{inputs_dir}/candidates/candidate-*.pdf"))
    results = []
    for i, pdf_path in enumerate(pdf_files, 1):
        print(f"  Procesando candidato {i}/{len(pdf_files)}: {Path(pdf_path).name}")
        text = read_pdf(pdf_path)
        result = classify_candidate(text, job_a, job_b)
        result["archivo"] = Path(pdf_path).name
        results.append(result)
    return results

def _build_candidate_blocks(candidates, score_key):
    blocks = []
    for i, c in enumerate(candidates, 1):
        emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        blocks.append({
            "object": "block", "type": "heading_3",
            "heading_3": {"rich_text": [{"text": {"content": f"{emoji} {c['nombre']} — Score: {c[score_key]}/10"}}]}
        })
        blocks.append({
            "object": "block", "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [{"text": {"content": f"✅ {c['fortalezas']}"}}]}
        })
        blocks.append({
            "object": "block", "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [{"text": {"content": f"⚠️ {c['riesgos']}"}}]}
        })
    return blocks

def _build_both_blocks(candidates):
    if not candidates:
        return [{"object": "block", "type": "paragraph",
                 "paragraph": {"rich_text": [{"text": {"content": "Ningún candidato aplica a ambos puestos."}}]}}]
    blocks = []
    for c in candidates:
        blocks.append({
            "object": "block", "type": "heading_3",
            "heading_3": {"rich_text": [{"text": {"content": f"⭐ {c['nombre']} — A: {c['score_a']}/10 | B: {c['score_b']}/10"}}]}
        })
        blocks.append({
            "object": "block", "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [{"text": {"content": f"✅ {c['fortalezas']}"}}]}
        })
        blocks.append({
            "object": "block", "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [{"text": {"content": f"⚠️ {c['riesgos']}"}}]}
        })
    return blocks

def _build_discarded_blocks(candidates):
    if not candidates:
        return [{"object": "block", "type": "paragraph",
                 "paragraph": {"rich_text": [{"text": {"content": "Ningún candidato descartado."}}]}}]
    blocks = []
    for c in candidates:
        blocks.append({
            "object": "block", "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [{"text": {"content": f"❌ {c['nombre']} — {c['riesgos']}"}}]}
        })
    return blocks

def publish_to_notion(results: list, parent_page_id: str):
    print("\n📤 Publicando reporte en Notion...")

    job_a_candidates = sorted([r for r in results if r["puesto_a"]], key=lambda x: x["score_a"], reverse=True)
    job_b_candidates = sorted([r for r in results if r["puesto_b"]], key=lambda x: x["score_b"], reverse=True)
    both = [r for r in results if r["puesto_a"] and r["puesto_b"]]
    none = [r for r in results if not r["puesto_a"] and not r["puesto_b"]]

    report_page = notion.pages.create(
        parent={"page_id": parent_page_id},
        properties={
            "title": {"title": [{"text": {"content": "📊 Reporte de Priorización de Candidatos"}}]}
        },
        children=[
            {"object": "block", "type": "heading_1",
             "heading_1": {"rich_text": [{"text": {"content": "📊 Reporte de Priorización de Candidatos"}}]}},
            {"object": "block", "type": "paragraph",
             "paragraph": {"rich_text": [{"text": {"content":
                f"Total evaluados: {len(results)} | Puesto A: {len(job_a_candidates)} | Puesto B: {len(job_b_candidates)} | Ambos: {len(both)} | Ninguno: {len(none)}"
             }}]}},
            {"object": "block", "type": "divider", "divider": {}},
            {"object": "block", "type": "heading_2",
             "heading_2": {"rich_text": [{"text": {"content": "🔵 Puesto A — Integration Developer Oracle EBS"}}]}},
        ] + _build_candidate_blocks(job_a_candidates, "score_a") + [
            {"object": "block", "type": "divider", "divider": {}},
            {"object": "block", "type": "heading_2",
             "heading_2": {"rich_text": [{"text": {"content": "🟢 Puesto B — Business Systems Analyst Oracle EBS"}}]}},
        ] + _build_candidate_blocks(job_b_candidates, "score_b") + [
            {"object": "block", "type": "divider", "divider": {}},
            {"object": "block", "type": "heading_2",
             "heading_2": {"rich_text": [{"text": {"content": "⭐ Aplican a Ambos Puestos"}}]}},
        ] + _build_both_blocks(both) + [
            {"object": "block", "type": "divider", "divider": {}},
            {"object": "block", "type": "heading_2",
             "heading_2": {"rich_text": [{"text": {"content": "⚪ Descartados"}}]}},
        ] + _build_discarded_blocks(none)
    )

    print(f"✅ Reporte publicado: {report_page['url']}")
    return report_page["url"]

if __name__ == "__main__":
    print("🚀 BetterWay Skill — Priorización Agéntica de Candidatos")
    print("=" * 55)

    INPUTS_DIR = "inputs"
    NOTION_PARENT_PAGE_ID = os.getenv("NOTION_PARENT_PAGE_ID")

    if not NOTION_PARENT_PAGE_ID:
        print("\n❌ Falta NOTION_PARENT_PAGE_ID en el .env")
        exit(1)

    print("\n📄 Leyendo y clasificando candidatos...")
    results = process_candidates(INPUTS_DIR)

    print(f"\n✅ {len(results)} candidatos procesados.")
    url = publish_to_notion(results, NOTION_PARENT_PAGE_ID)
    print(f"\n🎉 Listo. Reporte disponible en:\n   {url}")