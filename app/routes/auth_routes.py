from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.auth import authenticate_user

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = authenticate_user(request.form['username'], request.form['password'])
        if user:
            session.permanent = True
            session['logged_in'] = True
            session['user_role'] = user.role
            flash('Prihlásenie úspešné.', 'success')
            return redirect(url_for('main.evidency'))
        flash('Prihlásenie zlyhalo. Skontrolujte meno a heslo.', 'error')
    return render_template('login.html')


@bp.route('/logout')
def logout():
    session.clear()
    flash('Boli ste odhlásení.', 'success')
    return redirect(url_for('auth.login'))