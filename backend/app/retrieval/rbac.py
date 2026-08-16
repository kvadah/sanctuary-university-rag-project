"""Role-based document-classification access policy.

Maps a user's :class:`UserRole` to the set of :class:`DocumentClassification`
values they may retrieve. This is the single source of truth for retrieval-time
access control and is applied as a Qdrant payload filter. Pure function, so it is
unit-testable without any services.

Starting policy (documented for review): everyone sees PUBLIC and STUDENT
material; each staff-type role additionally sees its own tier; ADMIN sees all.
"""
from typing import Dict, List

from app.models.knowledge import DocumentClassification as DC
from app.models.user import UserRole

_POLICY: Dict[UserRole, List[DC]] = {
    UserRole.ADMIN: [DC.PUBLIC, DC.STUDENT, DC.FACULTY, DC.STAFF, DC.ADMIN],
    UserRole.FACULTY: [DC.PUBLIC, DC.STUDENT, DC.FACULTY],
    UserRole.STAFF: [DC.PUBLIC, DC.STUDENT, DC.STAFF],
    UserRole.STUDENT: [DC.PUBLIC, DC.STUDENT],
}


def allowed_classifications(role: UserRole) -> List[DC]:
    """Return the document classifications a user with ``role`` may retrieve."""
    return list(_POLICY[role])
