import json
import os
import uuid
from datetime import datetime
from typing import Optional



from dotenv import load_dotenv

# Load .env from repo root (one level up from backend/)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import Base, SessionLocal, engine, get_db
from models import JobDB, JobSchema, ProfileDB, ProfileSchema, RunDB, RunSchema
from runner import get_state, start_scraper

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Job Scraper & Analyzer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SCRAPERS = {
    "linkedin": {
        "id": "linkedin",
        "nombre": "LinkedIn & Indeed",
        "descripcion": "Scraper vía jobspy para LinkedIn e Indeed",
        "default_config": {
            "terminos": ["PR", "Marketing", "Comunicación Institucional", "Comunicación Externa"],
            "sitios": ["linkedin", "indeed"],
            "ubicacion": "Argentina",
            "resultados_por_busqueda": 30,
            "horas_atras": 96,
            "is_remote": False,
        },
    },
    "argentina": {
        "id": "argentina",
        "nombre": "ZonaJobs & Bumeran",
        "descripcion": "Scraper Selenium para ZonaJobs y Bumeran (Argentina)",
        "default_config": {
            "terminos": ["PR", "Marketing", "Comunicación Institucional", "Comunicación Externa"],
            "paginas_por_busqueda": 3,
            "obtener_descripcion": True,
        },
    },
}


# ─── Profile ──────────────────────────────────────────────────────────────────

@app.get("/api/profile", response_model=ProfileSchema)
def get_profile(db: Session = Depends(get_db)):
    profile = db.query(ProfileDB).filter(ProfileDB.id == 1).first()
    if not profile:
        profile = ProfileDB(id=1)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@app.put("/api/profile", response_model=ProfileSchema)
def update_profile(data: ProfileSchema, db: Session = Depends(get_db)):
    profile = db.query(ProfileDB).filter(ProfileDB.id == 1).first()
    if not profile:
        profile = ProfileDB(id=1)
        db.add(profile)
    for field, value in data.model_dump(exclude={"id"}).items():
        setattr(profile, field, value)
    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)
    return profile


# ─── Scrapers ─────────────────────────────────────────────────────────────────

@app.get("/api/scrapers")
def list_scrapers(db: Session = Depends(get_db)):
    result = []
    for info in SCRAPERS.values():
        last_run = (
            db.query(RunDB)
            .filter(RunDB.scraper_id == info["id"])
            .order_by(RunDB.started_at.desc())
            .first()
        )
        entry = {**info}
        if last_run:
            run_dict = RunSchema.model_validate(last_run).model_dump()
            state = get_state(last_run.id)
            run_dict["progress"] = state.get("progress", 100 if last_run.status != "running" else 0)
            run_dict["message"] = state.get("message", "")
            entry["last_run"] = run_dict
        else:
            entry["last_run"] = None
        result.append(entry)
    return result


@app.post("/api/scrapers/{scraper_id}/run")
def run_scraper(scraper_id: str, config: Optional[dict] = None, db: Session = Depends(get_db)):
    if scraper_id not in SCRAPERS:
        raise HTTPException(404, "Scraper no encontrado")

    already_running = (
        db.query(RunDB)
        .filter(RunDB.scraper_id == scraper_id, RunDB.status == "running")
        .first()
    )
    if already_running:
        raise HTTPException(400, "Ya hay un scraper corriendo para esta fuente")

    effective_config = config or SCRAPERS[scraper_id]["default_config"]
    run_id = str(uuid.uuid4())

    run = RunDB(
        id=run_id,
        scraper_id=scraper_id,
        config=json.dumps(effective_config),
        status="running",
        started_at=datetime.utcnow(),
    )
    db.add(run)
    db.commit()

    start_scraper(run_id, scraper_id, effective_config, SessionLocal)
    return {"run_id": run_id}


@app.get("/api/runs/{run_id}")
def get_run(run_id: str, db: Session = Depends(get_db)):
    run = db.query(RunDB).filter(RunDB.id == run_id).first()
    if not run:
        raise HTTPException(404, "Run no encontrado")

    # Refresh status from DB to pick up changes made in background thread
    db.refresh(run)
    state = get_state(run_id)
    result = RunSchema.model_validate(run).model_dump()
    result["progress"] = state.get("progress", 100 if run.status != "running" else 0)
    result["message"] = state.get("message", "")
    return result


# ─── Jobs ─────────────────────────────────────────────────────────────────────

@app.get("/api/jobs")
def list_jobs(
    fuente: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(JobDB)
    if fuente:
        q = q.filter(JobDB.fuente == fuente)
    if search:
        term = f"%{search}%"
        q = q.filter(
            JobDB.titulo.like(term) | JobDB.empresa.like(term) | JobDB.descripcion.like(term)
        )

    jobs = q.order_by(JobDB.created_at.desc()).all()
    return [JobSchema.model_validate(j) for j in jobs]


@app.get("/api/jobs/stats")
def jobs_stats(db: Session = Depends(get_db)):
    total = db.query(func.count(JobDB.id)).scalar() or 0
    by_source = db.query(JobDB.fuente, func.count(JobDB.id)).group_by(JobDB.fuente).all()
    return {
        "total": total,
        "by_source": {s: c for s, c in by_source if s},
    }


@app.delete("/api/jobs")
def clear_jobs(db: Session = Depends(get_db)):
    deleted = db.query(JobDB).delete()
    db.commit()
    return {"deleted": deleted}


