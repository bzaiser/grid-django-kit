# grid-django-kit

Wiederverwendbare Tabellen-, Such-, Sortier-, Paginierungs- & Export-Mixins (CSV/JSON) für Django + `django-design-studio`.

## Installation
```bash
pip install --no-user --upgrade --no-cache-dir git+https://github.com/bzaiser/grid-django-kit.git@main
```

```python
from django.views.generic import ListView
from grid_kit.mixins import DataGridMixin

class ItemListView(DataGridMixin, ListView):
    model = Item
    search_fields = ["name", "category"]
    allowed_sorts = ["name", "-name", "created_at", "-created_at"]
    export_fields = ["id", "name", "category"]
```
