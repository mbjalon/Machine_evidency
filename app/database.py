import sqlite3
from typing import List

import pandas as pd
from flask import g, current_app


def get_db():
    """Open a DB connection scoped to the current request (cached in g)."""
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'])
    return g.db


def query_to_dicts(cursor) -> List[dict]:
    """Convert a cursor result to a list of dicts."""
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def read_table(table_name: str) -> pd.DataFrame:
    """Read an entire table into a DataFrame."""
    return pd.read_sql_query(f'SELECT * FROM {table_name}', get_db())


def init_db():
    """Create all tables and seed initial data from Excel files."""
    db = get_db()

    # --- Table definitions ---
    standard_columns = '''
        registration_number TEXT,
        name TEXT,
        revision_date DATE,
        revision_periodicity INTEGER,
        protocol TEXT,
        type TEXT,
        manufacturing_number TEXT,
        manufacturer TEXT,
        location TEXT,
        owner TEXT,
        registration_date DATE,
        note TEXT
    '''

    tables_standard = [
        'small_machines',
        'big_machines',
        'temporary_archived_small_machines',
        'archived_small_machines',
        'temporary_archived_big_machines',
    ]

    for table in tables_standard:
        db.execute(f'CREATE TABLE IF NOT EXISTS {table} ({standard_columns})')

    # archived_big_machines has no revision_date column
    db.execute('''
               CREATE TABLE IF NOT EXISTS archived_big_machines (
                                                                    registration_number TEXT,
                                                                    name TEXT,
                                                                    revision_periodicity INTEGER,
                                                                    protocol TEXT,
                                                                    type TEXT,
                                                                    manufacturing_number TEXT,
                                                                    manufacturer TEXT,
                                                                    location TEXT,
                                                                    owner TEXT,
                                                                    registration_date DATE,
                                                                    note TEXT
               )
               ''')

    # --- Seed from Excel ---
    _seed_table(db, 'app/male.xlsx',    'small_machines',    has_revision_date=True)
    _seed_table(db, 'app/velke.xlsx',   'big_machines',      has_revision_date=True)
    _seed_table(db, 'app/a_male.xlsx',  'archived_small_machines', has_revision_date=True)
    _seed_table(db, 'app/ta_male.xlsx', 'temporary_archived_small_machines', has_revision_date=True)
    _seed_table(db, 'app/a_velke.xlsx', 'archived_big_machines', has_revision_date=False)

    db.commit()


def _seed_table(db, excel_path: str, table: str, has_revision_date: bool):
    """Read an Excel file and insert rows into the given table."""
    excel_file = pd.ExcelFile(excel_path)
    df = pd.read_excel(excel_file, sheet_name=excel_file.sheet_names[0], header=None)
    data = df.iloc[1:].values.tolist()

    print(f'Seeding {table} from {excel_path}...')

    if has_revision_date:
        sql = (
            f'INSERT INTO {table} (registration_number, name, revision_date, '
            'revision_periodicity, type, protocol, manufacturing_number, manufacturer, '
            'location, owner, registration_date, note) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
        )
        for row in data:
            reg_num, name, rev_date, rev_period, protocol, type_, man_num, manufacturer, location, owner, reg_date, note = row
            db.execute(sql, (reg_num, name, rev_date, rev_period, protocol, type_, man_num, manufacturer, location, owner, reg_date, note))
    else:
        sql = (
            f'INSERT INTO {table} (registration_number, name, revision_periodicity, '
            'protocol, type, manufacturing_number, manufacturer, location, owner, '
            'registration_date, note) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
        )
        for row in data:
            reg_num, name, rev_period, protocol, type_, man_num, manufacturer, location, owner, reg_date, note = row
            db.execute(sql, (reg_num, name, rev_period, protocol, type_, man_num, manufacturer, location, owner, reg_date, note))