"""
Generic machine blueprint factory.

Instead of copy-pasting routes for small_machines and big_machines,
we create one parameterised blueprint for each machine type.

Usage:
    from app.routes.machine_routes import make_machine_blueprint

    small_bp = make_machine_blueprint(
        name='small',
        table='small_machines',
        archive_table='archived_small_machines',
        temp_archive_table='temporary_archived_small_machines',
        list_template='small_machines.html',
        archive_template='archive_small.html',
        temp_archive_template='temporary_archive_small.html',
        edit_template='edit_machine_small.html',
    )
"""

from datetime import datetime
from flask import (
    Blueprint, flash, redirect, render_template,
    request, session, url_for,
)
from urllib.parse import urlencode

from app.auth import check_permission, login_required
from app.database import get_db, query_to_dicts
from app.machines import build_update_query, enrich_machine


def make_machine_blueprint(
        *,
        name: str,
        table: str,
        archive_table: str,
        temp_archive_table: str,
        list_template: str,
        archive_template: str,
        temp_archive_template: str,
        archive_has_revision_date: bool = True,
) -> Blueprint:
    """Return a Flask Blueprint with full CRUD + archive routes for a machine type."""

    bp = Blueprint(name, __name__)

    def _user_role():
        return session.get('user_role', 'user')

    def _list_url():
        """Redirect URL for list page, preserving the search query if present."""
        q = request.args.get('q') or request.form.get('q')
        return url_for(f'{name}.list_machines', q=q) if q else url_for(f'{name}.list_machines')

    def _template_ctx():
        return {'check_permission': check_permission, 'user_role': _user_role()}

    # ------------------------------------------------------------------
    # List view
    # ------------------------------------------------------------------

    @bp.route(f'/{table}')
    @login_required
    def list_machines():
        db = get_db()
        machines = query_to_dicts(db.execute(f'SELECT * FROM {table}'))
        machines = [enrich_machine(m) for m in machines]
        machines.sort(key=lambda m: (
            m['next_maintenance_date'] is None,
            m['next_maintenance_date'] or datetime.max,
        ))
        return render_template(list_template, machines=machines, **_template_ctx())

    # ------------------------------------------------------------------
    # Add
    # ------------------------------------------------------------------

    @bp.route(f'/add_{name}_machine', methods=['POST'])
    @login_required
    def add_machine():
        f = request.form
        db = get_db()
        db.execute(
            f'INSERT INTO {table} (registration_number, name, revision_date, '
            'revision_periodicity, type, protocol, manufacturing_number, manufacturer, '
            'location, owner, registration_date, note) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (f['registration_number'], f['name'], f['revision_date'], f['revision_periodicity'],
             f['type'], f['protocol'], f['manufacturing_number'], f['manufacturer'],
             f['location'], f['owner'], f['registration_date'], f['note']),
        )
        db.commit()
        flash('Zariadenie pridané úspešne.', 'success')
        return redirect(_list_url())

    # ------------------------------------------------------------------
    # Edit date only (quick form)
    # ------------------------------------------------------------------

    @bp.route(f'/edit_date_{name}_machine/<machine_id>', methods=['POST'])
    @login_required
    def edit_date(machine_id):
        db = get_db()
        db.execute(
            f'UPDATE {table} SET revision_date = ? WHERE registration_number = ?',
            (request.form['new_date'], machine_id),
        )
        db.commit()
        flash('Dátum revízie bol úspešne aktualizovaný.', 'success')
        return redirect(_list_url())

    # ------------------------------------------------------------------
    # Full edit
    # ------------------------------------------------------------------

    @bp.route(f'/edit_machine_{name}/<machine_id>', methods=['GET', 'POST'])
    @login_required
    def edit_machine(machine_id):
        if request.method == 'POST':
            fields = {
                'registration_number': request.form.get('new_reg_num'),
                'name':                request.form.get('new_name'),
                'revision_date':       request.form.get('new_revision_date'),
                'revision_periodicity': (
                    request.form.get('new_periodicity')
                    if (request.form.get('new_periodicity') or '').isdigit() else None
                ),
                'protocol':            request.form.get('new_protocol'),
                'type':                request.form.get('new_type'),
                'manufacturing_number': request.form.get('new_man_num'),
                'manufacturer':        request.form.get('new_man'),
                'location':            request.form.get('new_location'),
                'owner':               request.form.get('new_owner'),
                'registration_date':   request.form.get('new_reg_date'),
                'note':                request.form.get('new_note'),
            }

            sql, values = build_update_query(table, fields, 'registration_number')
            if values:
                db = get_db()
                db.execute(sql, values + [machine_id])
                db.commit()
                flash('Zariadenie bolo úspešne upravené.', 'success')
                return redirect(_list_url())

            flash('Žiadne polia neboli zmenené.', 'info')
            return redirect(url_for(f'{name}.edit_machine', machine_id=machine_id))

        db = get_db()
        cursor = db.execute(
            f'SELECT * FROM {table} WHERE registration_number = ?', (machine_id,)
        )
        columns = [col[0] for col in cursor.description]
        machine = dict(zip(columns, cursor.fetchone()))

        q = request.args.get('q', '')
        return render_template(
            'edit_machine.html',
            machine_id=machine_id,
            machine=machine,
            action_url=url_for(f'{name}.edit_machine', machine_id=machine_id, q=q),
            back_url=_list_url(),
            q=q,
            **_template_ctx(),
        )

    # ------------------------------------------------------------------
    # Remove (permanent delete)
    # ------------------------------------------------------------------

    @bp.route(f'/remove_machine_{name}<registration_number>')
    @login_required
    def remove_machine(registration_number):
        db = get_db()
        db.execute(f'DELETE FROM {table} WHERE registration_number = ?', (registration_number,))
        db.commit()
        flash('Zariadenie bolo úspešne vymazané.', 'success')
        return redirect(_list_url())

    @bp.route(f'/remove_machine_archive_{name}<machine_id>')
    @login_required
    def remove_from_archive(machine_id):
        db = get_db()
        db.execute(f'DELETE FROM {archive_table} WHERE registration_number = ?', (machine_id,))
        db.commit()
        flash('Zariadenie bolo úspešne vymazané.', 'success')
        return redirect(url_for(f'{name}.archive'))

    @bp.route(f'/remove_machine_temp_{name}<registration_number>')
    @login_required
    def remove_from_temp_archive(registration_number):
        db = get_db()
        db.execute(f'DELETE FROM {temp_archive_table} WHERE registration_number = ?', (registration_number,))
        db.commit()
        flash('Zariadenie bolo úspešne vymazané.', 'success')
        return redirect(url_for(f'{name}.temp_archive'))

    # ------------------------------------------------------------------
    # Archive views
    # ------------------------------------------------------------------

    @bp.route(f'/archive_{name}')
    @login_required
    def archive():
        db = get_db()
        machines = query_to_dicts(db.execute(f'SELECT * FROM {archive_table}'))
        return render_template(archive_template, machines=machines, **_template_ctx())

    @bp.route(f'/temporary_archive_{name}')
    @login_required
    def temp_archive():
        db = get_db()
        machines = query_to_dicts(db.execute(f'SELECT * FROM {temp_archive_table}'))
        return render_template(temp_archive_template, machines=machines, **_template_ctx())

    # ------------------------------------------------------------------
    # Archive / unarchive actions
    # ------------------------------------------------------------------

    @bp.route(f'/archive_machine_{name}/<machine_id>')
    @login_required
    def archive_machine(machine_id):
        db = get_db()
        machine = db.execute(
            f'SELECT * FROM {table} WHERE registration_number = ?', (machine_id,)
        ).fetchone()

        db.execute(f'DELETE FROM {table} WHERE registration_number = ?', (machine_id,))

        if archive_has_revision_date:
            db.execute(f'INSERT INTO {archive_table} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', machine)
        else:
            # archived_big_machines has no revision_date – drop index 2
            row = machine[:2] + machine[3:]
            db.execute(
                f'INSERT INTO {archive_table} (registration_number, name, revision_periodicity, '
                'type, protocol, manufacturing_number, manufacturer, location, owner, '
                'registration_date, note) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                row,
            )

        db.commit()
        flash('Zariadenie bolo úspešne vyradené.', 'success')
        return redirect(_list_url())

    @bp.route(f'/temp_archive_machine_{name}/<machine_id>')
    @login_required
    def temp_archive_machine(machine_id):
        db = get_db()
        machine = db.execute(
            f'SELECT * FROM {table} WHERE registration_number = ?', (machine_id,)
        ).fetchone()
        db.execute(f'DELETE FROM {table} WHERE registration_number = ?', (machine_id,))
        db.execute(f'INSERT INTO {temp_archive_table} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', machine)
        db.commit()
        flash('Zariadenie bolo dočasne vyradené.', 'success')
        return redirect(_list_url())

    @bp.route(f'/unarchive_temp_{name}/<machine_id>')
    @login_required
    def unarchive_temp(machine_id):
        db = get_db()
        machine = db.execute(
            f'SELECT * FROM {temp_archive_table} WHERE registration_number = ?', (machine_id,)
        ).fetchone()
        db.execute(f'DELETE FROM {temp_archive_table} WHERE registration_number = ?', (machine_id,))
        db.execute(f'INSERT INTO {table} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', machine)
        db.commit()
        flash('Zariadenie bolo úspešne vrátené do evidencie.', 'success')
        return redirect(url_for(f'{name}.temp_archive'))

    @bp.route(f'/unarchive_{name}/<machine_id>')
    @login_required
    def unarchive(machine_id):
        db = get_db()
        machine = db.execute(
            f'SELECT * FROM {archive_table} WHERE registration_number = ?', (machine_id,)
        ).fetchone()
        db.execute(f'DELETE FROM {archive_table} WHERE registration_number = ?', (machine_id,))
        db.execute(f'INSERT INTO {table} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', machine)
        db.commit()
        flash('Zariadenie bolo úspešne vrátené do evidencie.', 'success')
        return redirect(url_for(f'{name}.archive'))

    return bp