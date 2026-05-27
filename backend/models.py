import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from pydantic import BaseModel

from database import Base


class JobDB(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    fuente = Column(String)
    termino_busqueda = Column(String)
    titulo = Column(String)
    empresa = Column(String)
    ubicacion = Column(String)
    fecha = Column(String)
    url = Column(String, unique=True, index=True)
    descripcion = Column(Text)
    salario = Column(String)
    modalidad = Column(String)
    es_remoto = Column(Boolean)
    run_id = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    ai_score = Column(Integer)
    ai_justificacion = Column(Text)
    ai_tags = Column(String)  # JSON array as string
    ai_analyzed_at = Column(DateTime)


class ProfileDB(Base):
    __tablename__ = "profile"

    id = Column(Integer, primary_key=True, default=1)
    nombre = Column(String, default="")
    skills = Column(Text, default="")
    experiencia_anos = Column(Integer, default=0)
    nivel = Column(String, default="")
    modalidad_preferida = Column(String, default="")
    otras_preferencias = Column(Text, default="")
    updated_at = Column(DateTime, default=datetime.utcnow)


class RunDB(Base):
    __tablename__ = "runs"

    id = Column(String, primary_key=True)
    scraper_id = Column(String, index=True)
    status = Column(String, default="pending")  # running / completed / failed
    config = Column(Text)  # JSON
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime)
    total_jobs = Column(Integer, default=0)
    new_jobs = Column(Integer, default=0)
    error = Column(Text)


# ─── Pydantic schemas ────────────────────────────────────────────────────────

class JobSchema(BaseModel):
    id: str
    fuente: Optional[str] = None
    termino_busqueda: Optional[str] = None
    titulo: Optional[str] = None
    empresa: Optional[str] = None
    ubicacion: Optional[str] = None
    fecha: Optional[str] = None
    url: Optional[str] = None
    descripcion: Optional[str] = None
    salario: Optional[str] = None
    modalidad: Optional[str] = None
    es_remoto: Optional[bool] = None
    run_id: Optional[str] = None
    created_at: Optional[datetime] = None
    ai_score: Optional[int] = None
    ai_justificacion: Optional[str] = None
    ai_tags: Optional[str] = None
    ai_analyzed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProfileSchema(BaseModel):
    id: int = 1
    nombre: str = ""
    skills: str = ""
    experiencia_anos: int = 0
    nivel: str = ""
    modalidad_preferida: str = ""
    otras_preferencias: str = ""

    class Config:
        from_attributes = True


class RunSchema(BaseModel):
    id: str
    scraper_id: str
    status: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    total_jobs: int = 0
    new_jobs: int = 0
    error: Optional[str] = None

    class Config:
        from_attributes = True
