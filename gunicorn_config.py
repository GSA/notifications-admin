import os
import sys
import traceback
import multiprocessing
import gunicorn

# Let gunicorn figure out the right number of workers
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "eventlet"
bind = "0.0.0.0:{}".format(os.getenv("PORT"))
disable_redirect_access_to_syslog = True
gunicorn.SERVER_SOFTWARE = "None"


def worker_abort(worker):
    worker.log.info("worker received ABORT")
    for stack in sys._current_frames().values():
        worker.log.error("".join(traceback.format_stack(stack)))


# This issue is fixed in the 22.0.0 release, which we are using
# See github issue for details
# def fix_ssl_monkeypatching():
#     """
#     eventlet works by monkey-patching core IO libraries (such as ssl) to be non-blocking. However, there's currently
#     a bug: In the normal socket library it may throw a timeout error as a `socket.timeout` exception. However
#     eventlet.green.ssl's patch raises an ssl.SSLError('timed out',) instead. redispy handles socket.timeout but not
#     ssl.SSLError, so we solve this by monkey patching the monkey patching code to raise the correct exception type
#     :scream:
#     https://github.com/eventlet/eventlet/issues/692
#     """
#     # this has probably already been called somewhere in gunicorn internals, however, to be sure, we invoke it again.
#     # eventlet.monkey_patch can be called multiple times without issue
#     eventlet.monkey_patch()
#     eventlet.green.ssl.timeout_exc = socket.timeout


# fix_ssl_monkeypatching()
