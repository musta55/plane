# Non-interactive dummy-data seed for a local Plane dev stack.
#
# Usage (from repo root, backend stack already up):
#   docker compose -f docker-compose-local.yml exec -T api \
#     python manage.py shell --settings=plane.settings.local < seed_demo.py
#
# Creates a demo user (password login), a workspace, and one fully-populated project.
# Idempotent: clears prior projects in the workspace, then re-seeds.
#
# NOTE: create_dummy_data.create_module_issues does random.sample(modules, randint(0,5)),
# so module_count must be >= 5 or it raises "Sample larger than population".

from plane.db.models import User, Workspace, WorkspaceMember, Project
from plane.license.models import Instance, InstanceAdmin
from plane.bgtasks.dummy_data_task import create_dummy_data

email = "demo@plane.local"
password = "Demo12345!"
slug = "demo"

user, created = User.objects.get_or_create(
    email=email,
    defaults={"username": email, "display_name": "Demo User"},
)
user.is_active = True
user.is_email_verified = True
user.is_password_autoset = False
user.set_password(password)
user.save()
print("USER", user.email, "created" if created else "existing")

inst = Instance.objects.last()
if inst:
    InstanceAdmin.objects.get_or_create(user=user, instance=inst, defaults={"role": 20})
    # Mark the instance as set up so the main app and God-mode don't show the
    # first-run "create admin" screen.
    inst.is_setup_done = True
    inst.save()
    print("INSTANCE ok admin_set setup_done")
else:
    print("INSTANCE none - not registered yet")

ws, wcreated = Workspace.objects.get_or_create(
    slug=slug, defaults={"name": "Demo Workspace", "owner": user}
)
WorkspaceMember.objects.get_or_create(workspace=ws, member=user, defaults={"role": 20})
print("WORKSPACE", ws.slug, "created" if wcreated else "existing")

# idempotent: clear any prior projects (soft-delete manager returns int, not a tuple)
res = Project.objects.filter(workspace=ws).delete()
print("CLEARED", res)

before = Project.objects.filter(workspace=ws).count()
create_dummy_data(
    slug=slug,
    email=email,
    members=[],
    issue_count=40,
    cycle_count=4,
    module_count=6,   # must be >= 5 (see note above)
    pages_count=8,
    intake_issue_count=8,
)
after = Project.objects.filter(workspace=ws).count()
print("PROJECTS", before, "->", after)
print("SEED_DONE")
