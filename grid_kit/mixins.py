import csv
import json

from django.db.models import Q
from django.http import HttpResponse


def _resolve_attr(obj, field_path: str):
    val = obj
    for part in field_path.split("__"):
        val = getattr(val, part, "") if val is not None else ""
        if callable(val) and not getattr(val, "alters_data", False):
            val = val()
    return "" if val is None else val


def _sanitize_csv_cell(val):
    s = "" if val is None else str(val)
    stripped = s.lstrip()
    if stripped.startswith(("=", "+", "@", "\t", "\r")):
        return "'" + s
    if stripped.startswith("-") and not stripped[1:].replace(".", "", 1).replace(",", "", 1).isdigit():
        return "'" + s
    return s


def _safe_filename(name: str, default: str) -> str:
    cleaned = (name or "").replace('"', "").replace("\r", "").replace("\n", "").strip()
    return cleaned or default


def export_queryset_csv(queryset, fields, filename="export.csv") -> HttpResponse:
    resp = HttpResponse(content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="{_safe_filename(filename, "export.csv")}"'
    resp.write("\ufeff")
    writer = csv.writer(resp, delimiter=";")
    writer.writerow(fields)
    for obj in queryset.iterator(chunk_size=500):
        writer.writerow([_sanitize_csv_cell(_resolve_attr(obj, f)) for f in fields])
    return resp


def export_queryset_json(queryset, fields, filename="export.json") -> HttpResponse:
    rows = [{f: str(_resolve_attr(obj, f)) for f in fields} for obj in queryset.iterator(chunk_size=500)]
    resp = HttpResponse(json.dumps(rows, ensure_ascii=False, indent=2), content_type="application/json; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="{_safe_filename(filename, "export.json")}"'
    return resp


class DataGridMixin:
    search_fields = ()
    allowed_sorts = ()
    export_fields = ()
    export_filename = "export"
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset()
        q = (self.request.GET.get("q") or "").strip()
        if q and self.search_fields:
            cond = Q()
            for field in self.search_fields:
                cond |= Q(**{f"{field}__icontains": q})
            qs = qs.filter(cond)

        sort = (self.request.GET.get("sort") or "").strip()
        if sort and sort in self.allowed_sorts:
            qs = qs.order_by(sort)
        return qs

    def get(self, request, *args, **kwargs):
        fmt = (request.GET.get("export") or "").lower()
        if fmt in ("csv", "json") and self.export_fields:
            qs = self.get_queryset()
            if fmt == "csv":
                return export_queryset_csv(qs, self.export_fields, filename=f"{self.export_filename}.csv")
            return export_queryset_json(qs, self.export_fields, filename=f"{self.export_filename}.json")
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["grid_q"] = (self.request.GET.get("q") or "").strip()
        ctx["grid_sort"] = (self.request.GET.get("sort") or "").strip()
        ctx["grid_has_export"] = bool(self.export_fields)
        extra = self.request.GET.copy()
        for k in ("page", "export", "q", "sort"):
            extra.pop(k, None)
        ctx["grid_extra_query"] = extra.urlencode()
        ctx["grid_extra_params"] = [(k, v) for k, vals in extra.lists() for v in vals]
        return ctx
