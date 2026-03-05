from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

import config
from app.routes.machine_routes import make_machine_blueprint


def create_app() -> Flask:
    """Application factory."""
    import os
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'),
        static_folder=os.path.join(os.path.dirname(__file__), '..', 'static'),
    )
    app.config.from_object(config)

    # --- Register blueprints ---
    from app.routes.auth_routes import bp as auth_bp
    from app.routes.main_routes import bp as main_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    small_bp = make_machine_blueprint(
        name='small',
        table='small_machines',
        archive_table='archived_small_machines',
        temp_archive_table='temporary_archived_small_machines',
        list_template='small_machines.html',
        archive_template='archive_small.html',
        temp_archive_template='temporary_archive_small.html',
        archive_has_revision_date=True,
    )

    big_bp = make_machine_blueprint(
        name='big',
        table='big_machines',
        archive_table='archived_big_machines',
        temp_archive_table='temporary_archived_big_machines',
        list_template='big_machines.html',
        archive_template='archive_big.html',
        temp_archive_template='temporary_archive_big.html',
        archive_has_revision_date=False,
    )

    app.register_blueprint(small_bp)
    app.register_blueprint(big_bp)

    # --- Teardown: close DB connection after each request ---
    from app.database import get_db
    from flask import g

    @app.teardown_appcontext
    def close_db(error):
        db = g.pop('db', None)
        if db is not None:
            db.close()

    return app


def configure_scheduler(app: Flask) -> None:
    """Start background jobs for automatic Excel export and weekly email."""
    scheduler = BackgroundScheduler()

    def _export():
        with app.app_context():
            from app.services import export_to_excel
            export_to_excel()

    def _email():
        with app.app_context():
            from app.services import send_weekly_email
            send_weekly_email()

    scheduler.add_job(_export, CronTrigger(hour=5))
    scheduler.start()