"""Manages background scraper execution with progress tracking."""
import json
import threading
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, Optional

# In-memory progress state keyed by run_id
_state: Dict[str, Dict[str, Any]] = {}


def get_state(run_id: str) -> Dict[str, Any]:
    return _state.get(run_id, {})


def start_scraper(run_id: str, scraper_id: str, config: dict, db_factory: Callable) -> None:
    _state[run_id] = {"progress": 0, "message": "Iniciando...", "status": "running"}
    thread = threading.Thread(
        target=_execute,
        args=(run_id, scraper_id, config, db_factory),
        daemon=True,
    )
    thread.start()


def _execute(run_id: str, scraper_id: str, config: dict, db_factory: Callable) -> None:
    db = db_factory()
    try:
        from models import JobDB, RunDB

        def progress(pct: Optional[int], msg: str) -> None:
            if pct is not None:
                _state[run_id]["progress"] = pct
            _state[run_id]["message"] = msg

        if scraper_id == "linkedin":
            from scrapers.linkedin import run as scrape
        elif scraper_id == "argentina":
            from scrapers.argentina import run as scrape
        else:
            raise ValueError(f"Scraper desconocido: {scraper_id}")

        jobs = scrape(config, progress_callback=progress)

        new_count = 0
        for job_data in jobs:
            url = job_data.get("url")
            if not url:
                continue
            existing = db.query(JobDB).filter(JobDB.url == url).first()
            if not existing:
                db.add(JobDB(**job_data))
                new_count += 1

        db.commit()

        run = db.query(RunDB).filter(RunDB.id == run_id).first()
        if run:
            run.status = "completed"
            run.finished_at = datetime.utcnow()
            run.total_jobs = len(jobs)
            run.new_jobs = new_count
            db.commit()

        _state[run_id].update({"status": "completed", "progress": 100})

    except Exception as exc:
        _state[run_id].update({"status": "failed", "message": str(exc)})
        try:
            from models import RunDB

            run = db.query(RunDB).filter(RunDB.id == run_id).first()
            if run:
                run.status = "failed"
                run.error = str(exc)
                run.finished_at = datetime.utcnow()
                db.commit()
        except Exception:
            pass
    finally:
        db.close()
