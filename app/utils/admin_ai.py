# app/utils/admin_ai.py
from __future__ import annotations

from typing import Dict, List, Optional

from app.utils.control_plane import control_plane_state
from app.utils.settings import settings
from app.utils.sentinel import QuarantineRecord, ThreatRecord


class AdminAIReviewer:
    def review(
        self,
        *,
        project_slug: Optional[str],
        threats: List[ThreatRecord],
        quarantines: List[QuarantineRecord],
    ) -> Dict[str, object]:
        counts = {
            "threats": len(threats),
            "quarantines": len(quarantines),
            "critical": sum(1 for t in threats if t.severity == "critical"),
            "high": sum(1 for t in threats if t.severity == "high"),
            "review": sum(1 for t in threats if t.disposition == "review"),
            "quarantine": sum(1 for t in threats if t.disposition == "quarantine"),
        }

        recommended_actions: List[str] = []
        if counts["critical"] > 0:
            recommended_actions.append("Review critical incidents immediately in Ether admin.")
        if counts["quarantine"] > 0:
            recommended_actions.append("Confirm auto-quarantined actors and extend containment if needed.")
        if counts["high"] > 0:
            recommended_actions.append("Evaluate whether any provider or project control state should be toggled.")
        if not recommended_actions:
            recommended_actions.append("No urgent action recommended from the current Ether sentinel snapshot.")

        control_snapshot = control_plane_state.snapshot()
        summary = (
            f"Ether sentinel review for {project_slug or 'all projects'}: "
            f"{counts['threats']} threats logged, {counts['quarantines']} quarantines recorded, "
            f"{counts['critical']} critical and {counts['high']} high-severity events. "
            f"Current control state tracks {len(control_snapshot['projects'])} project overrides and "
            f"{len(control_snapshot['providers'])} provider overrides."
        )

        ai_mode = "openai_pending_credentials" if settings.ETHER_SENTINEL_AI_ENABLED else "deterministic_local"
        return {
            "ai_mode": ai_mode,
            "summary": summary,
            "recommended_actions": recommended_actions,
            "counts": counts,
        }


admin_ai_reviewer = AdminAIReviewer()
