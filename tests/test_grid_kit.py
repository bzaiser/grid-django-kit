import json
import os
import sys

import django
from django.conf import settings
from django.core.management import call_command
from django.test import RequestFactory, TestCase

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY="test-grid-kit",
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        INSTALLED_APPS=[
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "grid_kit",
        ],
        TEMPLATES=[{
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "APP_DIRS": True,
        }],
    )
    django.setup()

from django.contrib.auth import get_user_model
from django.views.generic import ListView
from grid_kit.mixins import DataGridMixin

User = get_user_model()


class UserGridView(DataGridMixin, ListView):
    model = User
    search_fields = ("username", "email")
    allowed_sorts = ("username", "-username")
    export_fields = ("username", "email")
    export_filename = "users"
    template_name = "grid_kit/includes/toolbar.html"


class GridKitTests(TestCase):
    def setUp(self):
        User.objects.create_user(username="anna", password="pw", email="anna@example.com")
        User.objects.create_user(username="bernd", password="pw", email="bernd@example.com")
        self.rf = RequestFactory()

    def test_search_sort_csv_and_json_export(self):
        view = UserGridView.as_view()

        req_csv = self.rf.get("/?q=anna&export=csv")
        resp_csv = view(req_csv)
        self.assertEqual(resp_csv.status_code, 200)
        text = resp_csv.content.decode("utf-8-sig")
        self.assertIn("anna@example.com", text)
        self.assertNotIn("bernd@example.com", text)

        req_json = self.rf.get("/?sort=-username&export=json")
        resp_json = view(req_json)
        rows = json.loads(resp_json.content.decode("utf-8"))
        self.assertEqual([r["username"] for r in rows], ["bernd", "anna"])


if __name__ == "__main__":
    from django.test.runner import DiscoverRunner
    call_command("migrate", verbosity=0)
    runner = DiscoverRunner(verbosity=2)
    sys.exit(bool(runner.run_tests(["tests.test_grid_kit"])))
