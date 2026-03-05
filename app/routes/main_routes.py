from flask import Blueprint, render_template, session

from app.auth import check_permission, login_required
from app.services import export_to_excel

bp = Blueprint('main', __name__)


@bp.route('/')
@login_required
def evidency():
    user_role = session.get('user_role', 'user')
    return render_template('evidency.html', check_permission=check_permission, user_role=user_role)


@bp.route('/create_excel_file')
@login_required
def create_excel_file():
    export_to_excel()
    from flask import redirect, url_for
    return redirect(url_for('main.evidency'))