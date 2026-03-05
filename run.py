from waitress import serve
from app import create_app, configure_scheduler

app = create_app()

if __name__ == '__main__':
    configure_scheduler(app)
    serve(app, host='0.0.0.0', port=8888)