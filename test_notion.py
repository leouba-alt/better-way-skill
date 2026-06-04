from notion_client import Client
import os
from dotenv import load_dotenv

load_dotenv()

notion = Client(auth=os.getenv("NOTION_TOKEN"))

results = notion.search(query="").get("results", [])
print(f"Conexión exitosa. Páginas encontradas: {len(results)}")