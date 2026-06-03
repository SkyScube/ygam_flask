def register_sockets(socketio):
    from src.sockets.chat import register_socket_events
    register_socket_events(socketio)
