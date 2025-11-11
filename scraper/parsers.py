import json
import re
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set

from selectolax.parser import HTMLParser

from .schema import OUTPUT_COLUMNS


OWNER_CORP_KEYWORDS = ["inc", "ltée", "québec inc", "corp", "corporation"]


def clean_text(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def parse_money(value: str) -> str:
    value = value.replace("\xa0", " ")
    digits = re.sub(r"[^0-9.-]", "", value)
    return digits


def parse_percentage(value: str) -> str:
    return re.sub(r"[^0-9.,]", "", value).replace(",", ".")


def parse_result_page(html: str) -> Dict[str, str]:
    tree = HTMLParser(html)
    data: Dict[str, str] = {col: "" for col in OUTPUT_COLUMNS}

    municipality_node = tree.css_first(
        "header.page-header .content-header-extras .list-inline-item div div:nth-child(1)"
    )
    if municipality_node:
        data["municipality"] = clean_text(municipality_node.text())

    fiscal_node = tree.css_first(
        "header.page-header .content-header-extras .list-inline-item div div:nth-child(2)"
    )
    if fiscal_node:
        data["fiscal_years"] = clean_text(fiscal_node.text())

    owners_section = _section_by_heading(tree, "proprietaires")
    owner_names: List[str] = []
    if owners_section:
        for item in owners_section.css("ul.list > li.list-item"):
            value_node = item.css_first(".list-item-content")
            value_text = clean_text(value_node.text() if value_node else "")
            if value_text:
                owner_names.append(value_text)
        if owner_names:
            data["owner_names"] = "; ".join(owner_names)
            owner_type = "person"
            lowered = data["owner_names"].lower()
            if any(keyword in lowered for keyword in OWNER_CORP_KEYWORDS):
                owner_type = "corporation"
            data["owner_type"] = owner_type
        else:
            data["owner_type"] = "unknown"
    else:
        data["owner_type"] = "unknown"

    identification_section = _section_by_heading(tree, "identification")
    if identification_section:
        mapping = _parse_dl_list(identification_section)
        if "Numéro de matricule" in mapping:
            data["matricule"] = mapping["Numéro de matricule"]
        if "Numéro de compte foncier" in mapping:
            data["tax_account_number"] = mapping["Numéro de compte foncier"]

    building_section = _section_by_heading(tree, "caracteristiques")
    if building_section:
        for heading in building_section.css("h3.h4"):
            if "Caractéristiques du bâtiment principal" in heading.text():
                list_mapping = _parse_dl_list(building_section)
                if "Nombre de logements" in list_mapping:
                    data["nb_logements"] = list_mapping["Nombre de logements"]

    value_section = _section_by_heading(tree, "valeur")
    if value_section:
        data.update(_parse_values(value_section))

    distribution_section = _find_section_with_table(value_section)
    if distribution_section:
        distribution = []
        table = distribution_section.css_first("table")
        if table:
            for row in table.css("tr"):
                cells = [clean_text(td.text()) for td in row.css("th, td")]
                if len(cells) >= 2 and cells[0].lower() != "sous-catégorie":
                    distribution.append(
                        {
                            "subcategory": cells[0],
                            "percentage": parse_percentage(cells[1]) if len(cells) > 1 else "",
                        }
                    )
        if distribution:
            data["tax_distribution_json"] = json.dumps(distribution, ensure_ascii=False)

    return data


def parse_result_json(payload: Dict[str, Any]) -> Dict[str, str]:
    normalized = _normalize_json_payload(payload)
    if _has_meaningful_data(normalized):
        return normalized

    html_candidates = list(_extract_html_candidates(payload))
    if not html_candidates:
        raise ValueError("No usable content found in JSON payload")
    for candidate in html_candidates:
        if not candidate:
            continue
        try:
            result = parse_result_page(candidate)
        except Exception:
            continue
        if _has_meaningful_data(result):
            return result
    raise ValueError("Unable to parse JSON payload with available content")


def _normalize_json_payload(payload: Dict[str, Any]) -> Dict[str, str]:
    data: Dict[str, str] = {col: "" for col in OUTPUT_COLUMNS}
    data["owner_type"] = "unknown"

    municipality = _find_string_by_keys(payload, ["municipality", "municipalite", "boroughName"])
    if not municipality:
        municipality = _find_value_by_label(payload, ["Municipalité", "Arrondissement"])
    data["municipality"] = municipality

    fiscal_years = _find_string_by_keys(payload, ["fiscalYears", "fiscal_years", "fiscalPeriod", "periodeRole"])
    if not fiscal_years:
        fiscal_years = _find_value_by_label(payload, ["Période du rôle", "Période du role", "Années financières"])
    data["fiscal_years"] = fiscal_years

    owners = _extract_owner_names(payload)
    if owners:
        data["owner_names"] = "; ".join(owners)
        lowered = data["owner_names"].lower()
        data["owner_type"] = "corporation" if any(keyword in lowered for keyword in OWNER_CORP_KEYWORDS) else "person"

    matricule = _find_string_by_keys(payload, ["matricule", "matriculeNumber", "matriculeNumberFormatted"])
    if not matricule:
        matricule = _find_value_by_label(payload, ["Numéro de matricule"])
    data["matricule"] = matricule

    tax_account = _find_string_by_keys(payload, ["taxAccountNumber", "numeroCompteFoncier", "taxAccount"])
    if not tax_account:
        tax_account = _find_value_by_label(payload, ["Numéro de compte foncier"])
    data["tax_account_number"] = tax_account

    nb_logements = _find_string_by_keys(payload, ["nbLogements", "nombreLogements", "numberOfDwellings"])
    if not nb_logements:
        nb_logements = _find_value_by_label(payload, ["Nombre de logements"])
    data["nb_logements"] = nb_logements

    role_courant = _find_node_by_title(payload, ["rôle courant", "role courant"])
    courant_mapping = _extract_labeled_values(role_courant) if role_courant else {}
    if courant_mapping:
        if "Terrain" in courant_mapping:
            data["assessed_terrain_current"] = parse_money(courant_mapping["Terrain"])
        if "Bâtiment" in courant_mapping or "Batiment" in courant_mapping:
            key = "Bâtiment" if "Bâtiment" in courant_mapping else "Batiment"
            data["assessed_batiment_current"] = parse_money(courant_mapping[key])
        if "Total" in courant_mapping:
            data["assessed_total_current"] = parse_money(courant_mapping["Total"])

    role_anterieur = _find_node_by_title(payload, ["rôle antérieur", "role anterieur", "rôle anterieur", "role antérieur"])
    anterieur_mapping = _extract_labeled_values(role_anterieur) if role_anterieur else {}
    if anterieur_mapping and "Total" in anterieur_mapping:
        data["assessed_total_previous"] = parse_money(anterieur_mapping["Total"])

    distribution_node = _find_node_by_title(payload, ["répartition", "repartition", "distribution"])
    distribution_rows = _extract_distribution_rows(distribution_node) if distribution_node else []
    if distribution_rows:
        data["tax_distribution_json"] = json.dumps(distribution_rows, ensure_ascii=False)

    return data


def _extract_html_candidates(node: Any, seen: Optional[Set[int]] = None) -> Iterable[str]:
    if seen is None:
        seen = set()
    obj_id = id(node)
    if obj_id in seen:
        return
    seen.add(obj_id)
    if isinstance(node, str):
        snippet = node.strip()
        if "<" in snippet and ">" in snippet and any(marker in snippet for marker in ("<section", "<header", "<dl", "<div", "</")):
            yield snippet
        return
    if isinstance(node, dict):
        for value in node.values():
            yield from _extract_html_candidates(value, seen)
    elif isinstance(node, list):
        for item in node:
            yield from _extract_html_candidates(item, seen)


def _has_meaningful_data(result: Dict[str, str]) -> bool:
    keys_to_check = {
        "owner_names",
        "matricule",
        "tax_account_number",
        "municipality",
        "assessed_total_current",
    }
    return any(result.get(key) for key in keys_to_check)


def _walk_nodes(node: Any) -> Iterable[Any]:
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk_nodes(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk_nodes(item)


def _find_string_by_keys(payload: Dict[str, Any], keys: Sequence[str]) -> str:
    lowered = [key.lower() for key in keys]
    for node in _walk_nodes(payload):
        if not isinstance(node, dict):
            continue
        for key, value in node.items():
            if key.lower() in lowered and isinstance(value, str):
                cleaned = clean_text(value)
                if cleaned:
                    return cleaned
    return ""


def _find_list_by_keys(payload: Dict[str, Any], keys: Sequence[str]) -> Optional[List[Any]]:
    lowered = [key.lower() for key in keys]
    for node in _walk_nodes(payload):
        if not isinstance(node, dict):
            continue
        for key, value in node.items():
            if key.lower() in lowered and isinstance(value, list) and value:
                return value
    return None


def _find_value_by_label(payload: Dict[str, Any], labels: Sequence[str]) -> str:
    labels_lower = [label.lower() for label in labels]
    for node in _walk_nodes(payload):
        if not isinstance(node, dict):
            continue
        candidate = None
        for key in ("label", "title", "name", "heading"):
            value = node.get(key)
            if isinstance(value, str) and any(label in value.lower() for label in labels_lower):
                candidate = value
                break
        if candidate:
            for value_key in ("value", "text", "content", "valueText"):
                value = node.get(value_key)
                if isinstance(value, str):
                    cleaned = clean_text(value)
                    if cleaned:
                        return cleaned
            values = node.get("values")
            if isinstance(values, list):
                texts = [clean_text(v) for v in values if isinstance(v, str) and clean_text(v)]
                if texts:
                    return "; ".join(texts)
    return ""


def _find_node_by_title(payload: Dict[str, Any], keywords: Sequence[str]) -> Optional[Dict[str, Any]]:
    keywords_lower = [keyword.lower() for keyword in keywords]
    for node in _walk_nodes(payload):
        if not isinstance(node, dict):
            continue
        for key in ("title", "label", "name", "heading", "id", "slug", "anchor"):
            value = node.get(key)
            if isinstance(value, str) and any(keyword in value.lower() for keyword in keywords_lower):
                return node
    return None


def _extract_labeled_values(node: Optional[Dict[str, Any]]) -> Dict[str, str]:
    if node is None:
        return {}
    mapping: Dict[str, str] = {}
    for sub_node in _walk_nodes(node):
        if not isinstance(sub_node, dict):
            continue
        label_text = None
        for key in ("label", "title", "name", "heading"):
            if key in sub_node and isinstance(sub_node[key], str):
                candidate = clean_text(sub_node[key])
                if candidate:
                    label_text = candidate
                    break
        if not label_text:
            continue
        for value_key in ("value", "text", "content", "valueText"):
            if value_key in sub_node and isinstance(sub_node[value_key], str):
                cleaned = clean_text(sub_node[value_key])
                if cleaned:
                    mapping[label_text] = cleaned
                    break
        else:
            values = sub_node.get("values")
            if isinstance(values, list):
                texts = [clean_text(v) for v in values if isinstance(v, str) and clean_text(v)]
                if texts:
                    mapping[label_text] = "; ".join(texts)
    return mapping


def _extract_distribution_rows(node: Optional[Dict[str, Any]]) -> List[Dict[str, str]]:
    if node is None:
        return []
    rows: List[Any] = []
    for sub_node in _walk_nodes(node):
        if not isinstance(sub_node, dict):
            continue
        for key in ("rows", "items", "body"):
            value = sub_node.get(key)
            if isinstance(value, list) and value:
                rows.extend(value)
        table = sub_node.get("table")
        if isinstance(table, dict):
            for table_key in ("rows", "body", "data"):
                value = table.get(table_key)
                if isinstance(value, list) and value:
                    rows.extend(value)
    distribution: List[Dict[str, str]] = []
    for row in rows:
        values = _row_to_values(row)
        if not values or len(values) < 2:
            continue
        header = values[0].lower()
        if header in {"sous-catégorie", "sous-categorie", "catégorie", "categorie"}:
            continue
        distribution.append(
            {
                "subcategory": values[0],
                "percentage": parse_percentage(values[1]) if values[1] else "",
            }
        )
    return distribution


def _row_to_values(row: Any) -> List[str]:
    if isinstance(row, dict):
        if "cells" in row and isinstance(row["cells"], list):
            return [value for value in (_coerce_string(cell) for cell in row["cells"]) if value]
        values: List[str] = []
        for key in ("label", "name", "title"):
            if key in row and isinstance(row[key], str):
                label = clean_text(row[key])
                if label:
                    values.append(label)
                    break
        for key in ("value", "text", "content", "valueText"):
            if key in row and isinstance(row[key], str):
                val = clean_text(row[key])
                if val:
                    if values:
                        values.append(val)
                    else:
                        values.extend(["", val])
                    break
        if not values and "values" in row and isinstance(row["values"], list):
            values = [clean_text(v) for v in row["values"] if isinstance(v, str) and clean_text(v)]
        return values
    if isinstance(row, list):
        return [value for value in (_coerce_string(cell) for cell in row) if value]
    if isinstance(row, str):
        parts = [part.strip() for part in row.split("|") if part.strip()]
        return [clean_text(part) for part in parts]
    return []


def _coerce_string(value: Any) -> str:
    if isinstance(value, str):
        return clean_text(value)
    if isinstance(value, dict):
        for key in ("value", "text", "content", "label", "name"):
            candidate = value.get(key)
            if isinstance(candidate, str):
                cleaned = clean_text(candidate)
                if cleaned:
                    return cleaned
    return ""


def _extract_owner_names(payload: Dict[str, Any]) -> List[str]:
    owners: List[str] = []
    direct_list = _find_list_by_keys(payload, ["owners", "proprietaires", "ownersList"])
    if direct_list:
        for entry in direct_list:
            candidate = _coerce_string(entry)
            if candidate and "numéro" not in candidate.lower():
                owners.append(candidate)
    if owners:
        return owners

    owner_section = _find_node_by_title(payload, ["propriétaire", "proprietaires", "owners"])
    if not owner_section:
        return owners
    for sub_node in _walk_nodes(owner_section):
        if not isinstance(sub_node, dict):
            continue
        for key in ("value", "text", "content", "name"):
            if key in sub_node and isinstance(sub_node[key], str):
                candidate = clean_text(sub_node[key])
                if candidate and "numéro" not in candidate.lower():
                    owners.append(candidate)
    return owners


def _section_by_heading(tree: HTMLParser, heading_id: str):
    heading = tree.css_first(f"h2#{heading_id}")
    if heading:
        return heading.parent
    return None


def _parse_dl_list(node) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for dt in node.css("dt"):
        dd = dt.next
        while dd is not None and dd.tag != "dd":
            dd = dd.next
        if dd is None:
            continue
        label = clean_text(dt.text())
        value = clean_text(dd.text())
        if label:
            result[label] = value
    return result


def _parse_values(section) -> Dict[str, str]:
    data: Dict[str, str] = {}
    for sub_section in section.css("section, div"):
        heading = sub_section.css_first("h3")
        if not heading:
            continue
        heading_text = clean_text(heading.text()).lower()
        dl_mapping = _parse_dl_list(sub_section)
        if "rôle courant" in heading_text:
            if "Terrain" in dl_mapping:
                data["assessed_terrain_current"] = parse_money(dl_mapping["Terrain"])
            if "Bâtiment" in dl_mapping:
                data["assessed_batiment_current"] = parse_money(dl_mapping["Bâtiment"])
            if "Total" in dl_mapping:
                data["assessed_total_current"] = parse_money(dl_mapping["Total"])
        if "rôle antérieur" in heading_text:
            if "Total" in dl_mapping:
                data["assessed_total_previous"] = parse_money(dl_mapping["Total"])
    return data


def _find_section_with_table(section):
    if section is None:
        return None
    if section.css_first("table"):
        return section
    for child in section.css("section, div"):
        if child.css_first("table"):
            return child
    return None
