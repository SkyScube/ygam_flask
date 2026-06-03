#!/usr/bin/env python3
import os
from src import create_app
from src.extensions import socketio

# create_tables only in the actual serving process, not in the reloader's
# stat/watcher process (WERKZEUG_RUN_MAIN is set only in the child process).
# In non-debug mode there is no reloader, so always create tables.
_is_reloader_child = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
_debug = os.environ.get('FLASK_DEBUG', 'true').lower() in ('1', 'true')
_should_init_db = _is_reloader_child or not _debug

app = create_app(create_tables=_should_init_db)

if __name__ == '__main__':
    socketio.run(app, debug=_debug, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
