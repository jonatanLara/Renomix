import os
import re
import shutil
import unicodedata
from typing import List, Dict, Any, Optional

INVALID_WIN_CHARS = r'<>:"/\\|?*'
INVALID_WIN_REGEX = re.compile(rf"[{re.escape(INVALID_WIN_CHARS)}]")
MULTISPACE = re.compile(r"\s{2,}")

def _strip_accents(s: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

def normalize_filename(name: str) -> str:
    s = _strip_accents(name)
    s = s.replace("\t", " ").replace("\n", " ").replace("\r", " ")
    s = INVALID_WIN_REGEX.sub("_", s)
    s = s.strip()
    s = MULTISPACE.sub(" ", s)
    return s

def split_name_ext(filename: str):
    # Mantiene el último punto como separador de extensión
    if filename.startswith('.') and filename.count('.') == 1:
        return filename, ''
    name, ext = os.path.splitext(filename)
    return name, ext

def ensure_dir(p: str):
    os.makedirs(p, exist_ok=True)

def with_increment(path: str) -> str:
    """Si existe, agrega (1), (2), ... antes de la extensión."""
    if not os.path.exists(path):
        return path
    dirn, base = os.path.dirname(path), os.path.basename(path)
    name, ext = split_name_ext(base)
    i = 1
    while True:
        candidate = os.path.join(dirn, f"{name} ({i}){ext}")
        if not os.path.exists(candidate):
            return candidate
        i += 1

def add_revert_suffix(path: str) -> str:
    dirn, base = os.path.dirname(path), os.path.basename(path)
    name, ext = split_name_ext(base)
    return os.path.join(dirn, f"{name} (revert){ext}")

class FileRenamer:
    def __init__(self, source_dir: str):
        self.source_dir = source_dir

    def _iter_files(self, recursive: bool, extensions: Optional[List[str]] = None):
        exts = None
        if extensions:
            exts = set([e.lower().strip() if e.startswith('.') else f'.{e.lower().strip()}' for e in extensions])
        if recursive:
            for root, _, files in os.walk(self.source_dir):
                for f in files:
                    if exts and os.path.splitext(f)[1].lower() not in exts:
                        continue
                    yield os.path.join(root, f)
        else:
            for f in os.listdir(self.source_dir):
                full = os.path.join(self.source_dir, f)
                if os.path.isfile(full):
                    if exts and os.path.splitext(f)[1].lower() not in exts:
                        continue
                    yield full

    def build_plan(
        self,
        prefix: str = "",
        suffix: str = "",
        separator: str = " ",
        pattern: str = "{prefix}{name}{suffix}{ext}",
        recursive: bool = False,
        extensions: Optional[List[str]] = None,
        destination_mode: str = "overwrite",  # overwrite | copy
        dest_dir: Optional[str] = None,
        conflict_policy: str = "increment",   # increment | overwrite | skip
    ) -> List[Dict[str, Any]]:
        plan: List[Dict[str, Any]] = []

        for src in self._iter_files(recursive=recursive, extensions=extensions):
            base = os.path.basename(src)
            name, ext = split_name_ext(base)

            n_prefix = normalize_filename(prefix)
            n_suffix = normalize_filename(suffix)
            n_name = normalize_filename(name)

            if n_prefix and n_name:
                final_sep = separator
            elif (n_prefix and not n_name) or (n_suffix and not n_name):
                final_sep = ""
            else:
                final_sep = separator

            new_base = pattern.format(
                prefix=(n_prefix + final_sep if n_prefix else ""),
                name=n_name,
                suffix=(final_sep + n_suffix if n_suffix else ""),
                ext=ext
            )
            new_base = normalize_filename(new_base)

            if destination_mode == "copy":
                if not dest_dir:
                    raise ValueError("dest_dir es requerido cuando destination_mode = 'copy'")
                ensure_dir(dest_dir)
                dst = os.path.join(dest_dir, new_base)
                operation = "copy"
            else:
                dst = os.path.join(os.path.dirname(src), new_base)
                operation = "rename"

            note = ""
            if os.path.abspath(src) == os.path.abspath(dst):
                note = "sin cambio"

            plan.append({
                "old_path": src,
                "new_path": dst,
                "operation": operation,
                "note": note,
            })
        return plan

    def apply_plan(self, plan: List[Dict[str, Any]], conflict_policy: str = "increment") -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for item in plan:
            src = item["old_path"]
            dst = item["new_path"]
            op = item["operation"]
            note = item.get("note", "")

            if not os.path.exists(src):
                results.append({**item, "status": "skip", "error": "origen no existe"})
                continue

            final_dst = dst
            if os.path.exists(dst):
                if conflict_policy == "skip":
                    results.append({**item, "status": "skip", "error": "destino existe"})
                    continue
                elif conflict_policy == "overwrite":
                    try:
                        os.remove(dst)
                    except Exception:
                        pass
                elif conflict_policy == "increment":
                    final_dst = with_increment(dst)
                else:
                    results.append({**item, "status": "error", "error": f"política desconocida: {conflict_policy}"})
                    continue

            try:
                if op == "copy":
                    ensure_dir(os.path.dirname(final_dst))
                    shutil.copy2(src, final_dst)
                else:
                    ensure_dir(os.path.dirname(final_dst))
                    os.replace(src, final_dst)
                results.append({**item, "status": "ok", "new_path": final_dst, "note": note})
            except Exception as e:
                results.append({**item, "status": "error", "error": str(e)})
        return results

    def undo_batch(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Revierte un lote: si fue copy -> elimina new_path; si fue rename -> renombra de vuelta.
        Si old_path existe al revertir, usa sufijo ' (revert)' con incremento para evitar colisiones.
        """
        out = []
        for r in rows:
            op = r.get("operation")
            old_p = r.get("old_path")
            new_p = r.get("new_path")
            try:
                if op == "copy":
                    if os.path.exists(new_p):
                        os.remove(new_p)
                        out.append({**r, "status": "ok", "action": "removed copy"})
                    else:
                        out.append({**r, "status": "skip", "action": "copy not found"})
                elif op == "rename":
                    if os.path.exists(new_p):
                        target = old_p if not os.path.exists(old_p) else with_increment(add_revert_suffix(old_p))
                        ensure_dir(os.path.dirname(target))
                        os.replace(new_p, target)
                        out.append({**r, "status": "ok", "action": f"renamed back -> {target}"})
                    else:
                        out.append({**r, "status": "skip", "action": "renamed file not found"})
                else:
                    out.append({**r, "status": "error", "action": f"op desconocida: {op}"})
            except Exception as e:
                out.append({**r, "status": "error", "action": str(e)})
        return out
