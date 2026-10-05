from app.core.config import get_settings
from app.models.agency import Agency


def design_v2_enabled_for_agency(agency: Agency | None) -> bool:
    """Se o visual novo das seções está liberado para a agência.

    Enquanto o rollout for "superusers", só agências com um superusuário entre os
    membros recebem o visual novo; as demais continuam no visual antigo.
    """
    rollout = get_settings().page_design_v2_rollout
    if rollout == "all":
        return True
    if rollout == "off" or agency is None:
        return False
    return any(rel.user is not None and bool(rel.user.is_superuser) for rel in agency.users or [])
