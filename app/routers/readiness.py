from __future__ import annotations

from fastapi import APIRouter

from app.utils.project_supabase_signal import project_signal_readiness
from app.utils.projects import get_project, list_projects

router = APIRouter(prefix="/readiness", tags=["readiness"])


@router.get("")
async def readiness_index():
    projects = list_projects()
    project_rows = []
    for project in projects:
        signal = project_signal_readiness(project.slug).to_dict()
        project_rows.append(
            {
                "slug": project.slug,
                "display_name": project.display_name,
                "status": project.status,
                "environment": project.environment,
                "enabled_providers": sorted([name for name, enabled in project.provider_set.items() if enabled]),
                "feature_flags": project.feature_flags,
                "signal": signal,
            }
        )

    return {
        "ok": True,
        "projects": project_rows,
        "count": len(project_rows),
    }


@router.get("/{project_slug}")
async def readiness_project(project_slug: str):
    project = get_project(project_slug)
    if project is None:
        return {
            "ok": False,
            "error": {
                "code": "ETHER_PROJECT_NOT_FOUND",
                "message": "Project could not be resolved.",
                "project_slug": project_slug,
            },
        }

    signal = project_signal_readiness(project.slug).to_dict()
    return {
        "ok": True,
        "project": {
            "slug": project.slug,
            "display_name": project.display_name,
            "status": project.status,
            "environment": project.environment,
            "enabled_providers": sorted([name for name, enabled in project.provider_set.items() if enabled]),
            "feature_flags": project.feature_flags,
            "signal": signal,
        },
    }
