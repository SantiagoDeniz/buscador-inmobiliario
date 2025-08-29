import os
import csv
import json
from datetime import datetime
from django.db import connection
from django.apps import apps


def _ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def _write_csv(file_path: str, headers: list[str], rows_iter):
    _ensure_dir(os.path.dirname(file_path))
    # utf-8-sig for Excel/Sheets friendliness
    with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(headers)
        for row in rows_iter:
            w.writerow(row)


def export_model_queryset(file_path: str, model, values_fields: list[str]):
    qs = model.objects.all().values(*values_fields)
    def rows():
        for obj in qs.iterator():
            yield [obj.get(k) for k in values_fields]
    _write_csv(file_path, values_fields, rows())


def export_core_models(base_dir: str):
    """Exportar modelos principales del dominio en CSVs separados."""
    from .models import (
        Inmobiliaria, Usuario, Plataforma, Busqueda, PalabraClave,
        BusquedaPalabraClave, Propiedad, ResultadoBusqueda,
    )
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_dir_latest = os.path.join(base_dir, 'latest')
    out_dir_stamp = os.path.join(base_dir, stamp)
    for out_dir in (out_dir_latest, out_dir_stamp):
        _ensure_dir(out_dir)

    # Define fields per model
    specs = [
        (Inmobiliaria, 'inmobiliaria', ['id', 'nombre', 'plan', 'created_at', 'updated_at']),
        (Usuario, 'usuario', ['id', 'nombre', 'email', 'password_hash', 'inmobiliaria_id', 'created_at', 'updated_at']),
        (Plataforma, 'plataforma', ['id', 'nombre', 'descripcion', 'url', 'created_at', 'updated_at']),
        (Busqueda, 'busqueda', ['id', 'nombre_busqueda', 'texto_original', 'filtros', 'guardado', 'usuario_id', 'created_at', 'updated_at']),
        (PalabraClave, 'palabra_clave', ['id', 'texto', 'idioma', 'sinonimos']),
        (BusquedaPalabraClave, 'busqueda_palabra_clave', ['id', 'busqueda_id', 'palabra_clave_id']),
        (Propiedad, 'propiedad', ['id', 'url', 'titulo', 'descripcion', 'metadata', 'plataforma_id', 'created_at', 'updated_at']),
        (ResultadoBusqueda, 'resultado_busqueda', ['id', 'busqueda_id', 'propiedad_id', 'coincide', 'metadata', 'created_at']),
    ]

    for model, name, fields in specs:
        # Serialize JSON fields to string
        def serialize_rows():
            for obj in model.objects.all().values(*fields).iterator():
                row = []
                for k in fields:
                    v = obj.get(k)
                    if isinstance(v, (dict, list)):
                        row.append(json.dumps(v, ensure_ascii=False))
                    else:
                        row.append(v)
                yield row
        for out_dir in (out_dir_latest, out_dir_stamp):
            _write_csv(os.path.join(out_dir, f'{name}.csv'), fields, serialize_rows())


def export_all_tables(base_dir: str):
    """Exportar todas las tablas visibles via introspección, incluyendo tablas de Django."""
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    out_dir_latest = os.path.join(base_dir, 'latest')
    out_dir_stamp = os.path.join(base_dir, stamp)
    for out_dir in (out_dir_latest, out_dir_stamp):
        _ensure_dir(out_dir)

    with connection.cursor() as cur:
        tables = connection.introspection.table_names()
        for table in tables:
            # Get headers once
            cur.execute(f"SELECT * FROM {table} LIMIT 0")
            headers = [d[0] for d in cur.description]
            for out_dir in (out_dir_latest, out_dir_stamp):
                # Re-run query per output to re-consume the cursor stream
                cur.execute(f"SELECT * FROM {table}")
                def rows():
                    while True:
                        batch = cur.fetchmany(5000)
                        if not batch:
                            break
                        for r in batch:
                            yield list(r)
                _write_csv(os.path.join(out_dir, f'{table}.csv'), headers, rows())


def export_all(base_dir: str):
    """Exporta modelos del dominio y todas las tablas a CSV."""
    export_core_models(base_dir)
    export_all_tables(base_dir)


def prune_old_exports(base_dir: str, keep: int = 1):
    """Elimina carpetas con timestamp antiguas en base_dir, conservando 'keep' más recientes.
    Mantiene siempre la carpeta 'latest'.
    """
    try:
        entries = []
        for name in os.listdir(base_dir):
            p = os.path.join(base_dir, name)
            if os.path.isdir(p) and name not in ("latest",):
                # Consider only timestamp-like names
                entries.append((name, p))
        # Sort by name descending (timestamps naturally sort)
        entries.sort(key=lambda x: x[0], reverse=True)
        to_delete = entries[keep:]
        for _, path in to_delete:
            # Recursively delete directory
            import shutil
            shutil.rmtree(path, ignore_errors=True)
    except Exception:
        # Best-effort clean; ignore errors
        pass


# -------------------- Auditoría de exports --------------------
import hashlib


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()


def _csv_stats(file_path: str):
    """Devuelve (num_rows, header, bytes_size). num_rows no incluye el header."""
    rows = 0
    header = None
    try:
        with open(file_path, 'r', encoding='utf-8-sig', newline='') as f:
            reader = csv.reader(f)
            try:
                header = next(reader)
            except StopIteration:
                header = []
                return 0, header, os.path.getsize(file_path)
            for _ in reader:
                rows += 1
    except Exception:
        # En caso de error, devolvemos lo que podamos
        try:
            size = os.path.getsize(file_path)
        except Exception:
            size = 0
        return rows, header or [], size
    size = 0
    try:
        size = os.path.getsize(file_path)
    except Exception:
        size = 0
    return rows, header or [], size


def _csv_duplicate_counts(file_path: str, header: list[str], pk_col: str | None = None):
    """Cuenta duplicados por fila completa y por PK (si se provee).
    Devuelve dict con keys: dup_full_row, dup_pk (o None si no aplica).
    """
    seen_rows = set()
    dup_full = 0
    dup_pk = None if not pk_col else 0
    pk_index = None
    if pk_col and header:
        try:
            pk_index = header.index(pk_col)
        except ValueError:
            pk_index = None
            dup_pk = None

    seen_pk = set() if pk_index is not None else None

    try:
        with open(file_path, 'r', encoding='utf-8-sig', newline='') as f:
            reader = csv.reader(f)
            # skip header
            try:
                next(reader)
            except StopIteration:
                return {"dup_full_row": 0, "dup_pk": dup_pk}
            for row in reader:
                t = tuple(row)
                if t in seen_rows:
                    dup_full += 1
                else:
                    seen_rows.add(t)

                if pk_index is not None and seen_pk is not None:
                    key = row[pk_index] if pk_index < len(row) else None
                    if key is not None:
                        if key in seen_pk:
                            dup_pk += 1  # type: ignore[operator]
                        else:
                            seen_pk.add(key)
    except Exception:
        # Best-effort
        pass
    return {"dup_full_row": dup_full, "dup_pk": dup_pk}


def audit_exports(base_dir: str) -> dict:
    """Genera un manifiesto de auditoría para los CSVs en base_dir/latest.
    - Cuenta filas en CSV (sin header)
    - Calcula SHA-256 de cada archivo
    - Compara con conteo en DB si el archivo corresponde a una tabla (p.ej., <tabla>.csv)
    - Detecta duplicados por fila completa y por PK (si disponible vía introspección)
    Escribe _manifest.json y _manifest.csv en latest, y devuelve el dict del manifiesto.
    """
    latest_dir = os.path.join(base_dir, 'latest')
    _ensure_dir(latest_dir)

    manifest = {
        "generated_at": datetime.now().isoformat(),
        "base_dir": base_dir,
        "latest_dir": latest_dir,
        "files": [],
        "db": {"tables": {}},
        "summary": {},
    }

    # Mapear tablas -> pk y conteos en DB
    table_pk_map: dict[str, str | None] = {}
    table_db_counts: dict[str, int] = {}
    try:
        with connection.cursor() as cur:
            tables = connection.introspection.table_names()
            for t in tables:
                try:
                    pk_col = connection.introspection.get_primary_key_column(cur, t)
                except Exception:
                    pk_col = None
                table_pk_map[t] = pk_col
                try:
                    cur.execute(f"SELECT COUNT(*) FROM {t}")
                    cnt = cur.fetchone()[0]  # type: ignore[index]
                except Exception:
                    cnt = -1
                table_db_counts[t] = int(cnt)
            manifest["db"]["tables"] = {
                t: {"primary_key": table_pk_map.get(t), "row_count": table_db_counts.get(t, -1)} for t in tables
            }
    except Exception:
        # Si falla introspección, continuamos con auditoría de archivos únicamente
        pass

    # Recorrer CSVs en latest
    files = []
    try:
        files = [f for f in os.listdir(latest_dir) if f.lower().endswith('.csv')]
    except Exception:
        files = []

    manifest_rows_csv = [
        [
            "file",
            "bytes",
            "rows_csv",
            "sha256",
            "db_table",
            "db_rows",
            "rows_match",
            "dup_full_row",
            "dup_pk",
        ]
    ]

    total_files = 0
    total_rows = 0
    mismatches = 0
    duplicates_any = 0

    for name in sorted(files):
        path = os.path.join(latest_dir, name)
        rows_csv, header, size_bytes = _csv_stats(path)
        sha = _sha256_file(path)

        # Si el nombre coincide con una tabla, comparar con DB
        table_name = name[:-4] if name.lower().endswith('.csv') else None
        db_rows = table_db_counts.get(table_name, None) if table_name else None
        pk_col = table_pk_map.get(table_name, None) if table_name else None

        dup_info = _csv_duplicate_counts(path, header, pk_col)
        rows_match = (db_rows is not None and db_rows >= 0 and rows_csv == db_rows)
        if not rows_match and db_rows is not None and db_rows >= 0:
            mismatches += 1
        if (dup_info.get("dup_full_row", 0) or (dup_info.get("dup_pk") or 0)):
            duplicates_any += 1

        entry = {
            "file": name,
            "bytes": size_bytes,
            "rows_csv": rows_csv,
            "sha256": sha,
            "db_table": table_name,
            "db_rows": db_rows,
            "rows_match": rows_match,
            "dup_full_row": dup_info.get("dup_full_row"),
            "dup_pk": dup_info.get("dup_pk"),
        }
        manifest["files"].append(entry)
        manifest_rows_csv.append([
            name,
            size_bytes,
            rows_csv,
            sha,
            table_name or "",
            "" if db_rows is None else db_rows,
            rows_match,
            dup_info.get("dup_full_row"),
            dup_info.get("dup_pk"),
        ])

        total_files += 1
        total_rows += max(0, rows_csv)

    manifest["summary"] = {
        "files": total_files,
        "rows_total_csv": total_rows,
        "db_tables_counted": len(table_db_counts) if table_db_counts else 0,
        "csv_db_mismatches": mismatches,
        "files_with_duplicates": duplicates_any,
    }

    # Escribir manifiestos
    try:
        with open(os.path.join(latest_dir, "_manifest.json"), 'w', encoding='utf-8') as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
    except Exception:
        pass
    try:
        with open(os.path.join(latest_dir, "_manifest.csv"), 'w', encoding='utf-8-sig', newline='') as f:
            w = csv.writer(f)
            w.writerows(manifest_rows_csv)
    except Exception:
        pass

    return manifest
