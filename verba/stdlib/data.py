import csv as _py_csv
import os


def _auto_type(value):
    if not isinstance(value, str):
        return value
    v = value.strip()
    if not v:
        return value
    try:
        return int(v) if "." not in v else float(v)
    except (ValueError, TypeError):
        return value


def data_read_csv(path):
    if not os.path.exists(path):
        raise Exception(f"File not found: {path}")
    with open(path, newline="", encoding="utf-8") as f:
        return [
            {k: _auto_type(v) for k, v in row.items()}
            for row in _py_csv.DictReader(f)
            if any(v.strip() for v in row.values())
        ]


def data_write_csv(path, rows):
    if not rows:
        raise Exception("No data to write.")
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = _py_csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    return f"Wrote {len(rows)} rows to {path}"


def _sort_key(x, key):
    v = x.get(key) if isinstance(x, dict) else x
    return (0, v) if v is not None else (1, "")


def data_sort(data_list, key):
    if not isinstance(data_list, list):
        raise Exception("Expected a list.")
    data_list.sort(key=lambda x: _sort_key(x, key))
    return data_list


def data_sort_desc(data_list, key):
    if not isinstance(data_list, list):
        raise Exception("Expected a list.")
    data_list.sort(key=lambda x: _sort_key(x, key), reverse=True)
    return data_list


def data_filter(data_list, key, value):
    if not isinstance(data_list, list):
        raise Exception("Expected a list.")
    return [row for row in data_list if (row.get(key) if isinstance(row, dict) else row) == value]


def data_select(data_list, key):
    if not isinstance(data_list, list):
        raise Exception("Expected a list.")
    return [row.get(key) for row in data_list if isinstance(row, dict)]


FUNCTIONS = {
    "read_csv":   (data_read_csv,   ["path"]),
    "write_csv":  (data_write_csv,  ["path", "rows"]),
    "sort":       (data_sort,       ["data_list", "key"]),
    "sort_desc":  (data_sort_desc,  ["data_list", "key"]),
    "filter":     (data_filter,     ["data_list", "key", "value"]),
    "select":     (data_select,     ["data_list", "key"]),
}
