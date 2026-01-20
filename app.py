from main import create_app, socketio, Config

app = create_app()

if __name__ == '__main__':
    socketio.run(app, host=Config.APP_HOST, debug=False)