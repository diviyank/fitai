import json
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, Response
from sqlmodel import Session

from ..db import get_session
from ..models import User
from ..auth import current_user
from ..main import templates
from .. import jobs

router = APIRouter()


def render_panel(request: Request, kind: str, job, *, session=None, **extra) -> HTMLResponse:
    """Build the template context for a panel from a job row (or None)."""
    result = json.loads(job.result_json) if job and job.result_json else None
    params = json.loads(job.params_json) if job and job.params_json else {}
    ctx = {
        "request": request, "kind": kind, "job": job,
        "result": result, "params": params,
        "prompt": job.prompt if job else "",
        "notice": job.notice if job else None,
    }
    from .. import panels
    ctx.update(panels.extra_context(kind, params, result))
    if kind == "plan" and result and result.get("plan_id") and session is not None:
        from ..models import TrainingPlan
        plan = session.get(TrainingPlan, result["plan_id"])
        if plan:
            ctx.update({"plan": plan, "plans": plan.proposals_json})
    ctx.update(extra)
    return templates.TemplateResponse("partials/_panel.html", ctx)


@router.get("/jobs/{kind}/panel", response_class=HTMLResponse)
def panel(kind: str, request: Request, session: Session = Depends(get_session),
          user: User = Depends(current_user)):
    job = jobs.latest(session, kind)
    if kind == "nutrition" and job and job.status == "done":
        return Response(status_code=204, headers={"HX-Redirect": "/nutrition"})
    return render_panel(request, kind, job, session=session)
