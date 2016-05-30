import config
import queue
import threading

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

# master_thread.start()
# filter(lambda a: a.start(), slave_threads)
