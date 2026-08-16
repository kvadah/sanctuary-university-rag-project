from app.models.knowledge import DocumentClassification as DC
from app.models.user import UserRole
from app.retrieval.rbac import allowed_classifications


def test_admin_sees_all_classifications():
    assert set(allowed_classifications(UserRole.ADMIN)) == set(DC)


def test_student_is_restricted_to_public_and_student():
    allowed = allowed_classifications(UserRole.STUDENT)
    assert set(allowed) == {DC.PUBLIC, DC.STUDENT}
    assert DC.FACULTY not in allowed
    assert DC.ADMIN not in allowed


def test_faculty_and_staff_scopes_do_not_leak_into_each_other():
    faculty = allowed_classifications(UserRole.FACULTY)
    staff = allowed_classifications(UserRole.STAFF)

    assert DC.FACULTY in faculty and DC.STAFF not in faculty
    assert DC.STAFF in staff and DC.FACULTY not in staff
    # non-admin roles never see ADMIN-classified documents
    assert DC.ADMIN not in faculty and DC.ADMIN not in staff


def test_every_role_can_see_public():
    for role in UserRole:
        assert DC.PUBLIC in allowed_classifications(role)
