import config
import queue
import threading
import logging

logging.basicConfig(level=logging.INFO)

# Init Queue
q = queue.Queue()
# Initialize Plug-ins Library
# (Load libraries and modules and init them with Queue `q`)
slaves = {}
for i in config.slave_channels:
    obj = getattr(__import__(i[0], fromlist=i[1]), i[1])
    slaves[obj.channel_id] = obj(q)
master = getattr(__import__(config.master_channel[0], fromlist=config.master_channel[1]), config.master_channel[1])(q, slaves)

master_thread = threading.Thread(target=master.poll)
slave_threads = {key: threading.Thread(target=slaves[key].poll) for key in slaves}

master_thread.start()
for i in slave_threads:
    slave_threads[i].start()
