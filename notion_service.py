import httpx
import os
from datetime import datetime


NOTION_API_URL = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def _headers():
    return {
        "Authorization": f"Bearer {os.getenv('NOTION_API_KEY')}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }


async def crear_tarea(
    titulo: str,
    descripcion: str = "",
    estado: str = "Por hacer",
    prioridad: str = "Media",
    fecha_limite: str | None = None,
    categoria: str = "Trabajo",
    origen: str = "WhatsApp",
) -> dict:
    """Crea una tarea en la base de datos de Notion."""

    database_id = os.getenv("NOTION_DATABASE_ID")

    properties = {
        "Nombre": {
            "title": [{"text": {"content": titulo}}]
        },
        "Estado": {
            "select": {"name": estado}
        },
        "Prioridad": {
            "select": {"name": prioridad}
        },
        "Categoría": {
            "select": {"name": categoria}
        },
        "Origen": {
            "select": {"name": origen}
        },
    }

    if fecha_limite:
        properties["Fecha límite"] = {
            "date": {"start": fecha_limite}
        }

    body = {
        "parent": {"database_id": database_id},
        "properties": properties,
    }

    # Añadir descripción como contenido de la página
    if descripcion:
        body["children"] = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": descripcion}}]
                },
            }
        ]

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{NOTION_API_URL}/pages",
            headers=_headers(),
            json=body,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

    return {
        "id": data["id"],
        "url": data["url"],
        "titulo": titulo,
    }


async def listar_tareas(estado: str | None = None, limite: int = 10) -> list[dict]:
    """Lista tareas de la base de datos de Notion."""

    database_id = os.getenv("NOTION_DATABASE_ID")

    body: dict = {"page_size": limite}

    if estado:
        body["filter"] = {
            "property": "Estado",
            "select": {"equals": estado},
        }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{NOTION_API_URL}/databases/{database_id}/query",
            headers=_headers(),
            json=body,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

    tareas = []
    for page in data.get("results", []):
        props = page["properties"]
        titulo = ""
        if props.get("Nombre", {}).get("title"):
            titulo = props["Nombre"]["title"][0]["plain_text"]

        tareas.append({
            "id": page["id"],
            "titulo": titulo,
            "estado": props.get("Estado", {}).get("select", {}).get("name", ""),
            "prioridad": props.get("Prioridad", {}).get("select", {}).get("name", ""),
            "url": page["url"],
        })

    return tareas
