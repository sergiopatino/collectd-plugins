# $__FILE__

import Queue as queue 
import threading
import collectd

class BaseWriter(threading.Thread):
    """
    Base class for all writers.

    :param formatter: Formatter instance.

    """


    MAX_BUFFER_SIZE = 1000
    """The maximum size of values in the output buffer."""


    def __init__(self, formatter):
        collectd.debug("BaseWriter.__init__: formatter=%s, MAX_BUFFER_SIZE=%s" % 
                       (formatter, self.MAX_BUFFER_SIZE))

        threading.Thread.__init__(self)
        self.buffer = queue.Queue(maxsize=self.MAX_BUFFER_SIZE)
        self.formatter = formatter


    def shutdown(self):
        """
        `shutdown()` will be called by `run()`.

        This can be overridden by a derived class.
        """
        pass

    
    def flush(self, message):
        """
        `flush()` will be called by `run()` when the write buffer must be flushed.

        :param message: 

        This must be overridden by a derived class.
        """

        raise NotImplementedError


    def write(self, values_dict):
        collectd.debug('%s.write_callback: values_object=%s' % ('$NAME', values_dict))

        try:
            self.buffer.put_nowait(values_dict)
        except queue.Full:
            collectd.notice("%s output buffer full" % (self))


    def run(self):
        collectd.debug("BaseWriter.run")

        while True: 
            try:
                values_dict = self.buffer.get(block=True, timeout=0.1)
                self.flush(values_dict)
            except queue.Empty:
                pass

