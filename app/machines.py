from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import Optional, Tuple


def parse_revision_date(date_str: str) -> Optional[datetime]:
    """Try to parse a revision date string in either of the two expected formats."""
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d'):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def calculate_validation(machine: dict) -> Optional[datetime]:
    """Return the next validation deadline for a machine dict."""
    revision_date = parse_revision_date(str(machine['revision_date']))
    if revision_date is None:
        print(f"Could not parse revision_date for {machine.get('registration_number')}")
        return None
    return revision_date + relativedelta(months=machine['revision_periodicity'])


def enrich_machine(machine: dict) -> dict:
    """Add maintenance status fields to a machine dict (mutates in place)."""
    now = datetime.now()
    validation = calculate_validation(machine)
    machine['next_maintenance_date'] = validation

    if validation is not None:
        machine['next_maintenance_overdue'] = now > validation
        machine['next_maintenance_soon'] = validation < now + timedelta(days=30)
        machine['add_revision_date'] = False
    else:
        machine['next_maintenance_overdue'] = False
        machine['next_maintenance_soon'] = False
        machine['add_revision_date'] = True

    return machine


def build_update_query(table: str, fields: dict, where_column: str) -> Tuple[str, list]:
    """
    Build a parameterised UPDATE statement from a dict of {column: value}.
    Only non-empty values are included.

    Returns (sql_string, list_of_values_with_where_value_appended).
    The caller must append the WHERE value to the returned list before executing.
    """
    updates = {col: val for col, val in fields.items() if val is not None}
    if not updates:
        return '', []

    set_clause = ', '.join(f'{col} = ?' for col in updates)
    sql = f'UPDATE {table} SET {set_clause} WHERE {where_column} = ?'
    return sql, list(updates.values())