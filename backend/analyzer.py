"""Claude-powered job relevance analyzer."""
import json
import os
from typing import Dict, List

import anthropic

BATCH_SIZE = 15


def analyze_jobs(jobs: List[Dict], profile: Dict) -> List[Dict]:
    """Returns list of {job_id, score, justificacion, tags}."""
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    results: List[Dict] = []

    for i in range(0, len(jobs), BATCH_SIZE):
        batch = jobs[i : i + BATCH_SIZE]
        results.extend(_analyze_batch(client, batch, profile))

    return results


def _analyze_batch(client: anthropic.Anthropic, jobs: List[Dict], profile: Dict) -> List[Dict]:
    jobs_text = "\n\n".join(
        f"**JOB_ID:{job['id']}**\n"
        f"Título: {job.get('titulo') or ''}\n"
        f"Empresa: {job.get('empresa') or ''}\n"
        f"Ubicación: {job.get('ubicacion') or ''}\n"
        f"Modalidad: {job.get('modalidad') or ''} {'(Remoto)' if job.get('es_remoto') else ''}\n"
        f"Salario: {job.get('salario') or 'No especificado'}\n"
        f"Descripción: {(job.get('descripcion') or '')[:600]}"
        for job in jobs
    )

    profile_text = (
        f"Nombre: {profile.get('nombre', '')}\n"
        f"Skills: {profile.get('skills', '')}\n"
        f"Años de experiencia: {profile.get('experiencia_anos', 0)}\n"
        f"Nivel: {profile.get('nivel', '')}\n"
        f"Modalidad preferida: {profile.get('modalidad_preferida', '')}\n"
        f"Otras preferencias: {profile.get('otras_preferencias', '')}"
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        tools=[
            {
                "name": "score_jobs",
                "description": "Puntúa la relevancia de ofertas de trabajo para un perfil específico",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "resultados": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "job_id": {"type": "string"},
                                    "score": {"type": "integer", "minimum": 0, "maximum": 100},
                                    "justificacion": {"type": "string"},
                                    "tags": {"type": "array", "items": {"type": "string"}},
                                },
                                "required": ["job_id", "score", "justificacion", "tags"],
                            },
                        }
                    },
                    "required": ["resultados"],
                },
            }
        ],
        tool_choice={"type": "tool", "name": "score_jobs"},
        messages=[
            {
                "role": "user",
                "content": (
                    f"Analiza las siguientes ofertas de trabajo y puntúa su relevancia (0-100) para este perfil.\n\n"
                    f"PERFIL:\n{profile_text}\n\n"
                    f"OFERTAS:\n{jobs_text}\n\n"
                    "Criterios:\n"
                    "90-100: Match perfecto con skills, experiencia y preferencias\n"
                    "70-89: Alta relevancia, cumple la mayoría de criterios\n"
                    "50-69: Relevancia media, vale la pena revisar\n"
                    "30-49: Baja relevancia, algunos aspectos coinciden\n"
                    "0-29: No relevante o sin información suficiente"
                ),
            }
        ],
    )

    tool_use = next((b for b in response.content if b.type == "tool_use"), None)
    if not tool_use:
        return []
    return tool_use.input.get("resultados", [])
