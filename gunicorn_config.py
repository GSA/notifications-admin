import multiprocessing
import os
import sys
import traceback
import logging
from app.utils import hilite
import gunicorn

# Let gunicorn figure out the right number of workers
# The recommended formula is cpu_count() * 2 + 1
# but we have an unusual configuration with a lot of cpus and not much memory
# so adjust it.
workers = multiprocessing.cpu_count()
worker_class = "gevent"

logging.basicConfig(level=logging.INFO)
logging.info(hilite("Gunicorn timeout set to 240 seconds"))
timeout = 240
bind = "0.0.0.0:{}".format(os.getenv("PORT"))
disable_redirect_access_to_syslog = True
gunicorn.SERVER_SOFTWARE = "None"


def worker_abort(worker):
    worker.log.info("worker received ABORT")
    for stack in sys._current_frames().values():
        worker.log.error("".join(traceback.format_stack(stack)))
