
# $__FILE__

import collectd
import socket

class TcpWriter(BaseWriter):
    """
    Send JSON inside UDP packet.

    :param formatter: Formatter instance.
    :param host: Host to send data to.
    :param port: Port to connect to.

    """

    def __init__(self, formatter, host, port):
        collectd.debug("%s formatter=%s host=%s, port=%s" % 
                       ('$NAME', formatter, host, port))

        super(TcpWriter, self).__init__(formatter)

        self.host = host
        self.port = int(port)

        self.sock = self.connect()

    def connect(self):
        try:
            self.sock = socket.create_connection((self.host, self.port))
        except socket.error:
            self.sock = None

    def disconnect(self):
        if self.sock:
            self.sock.shutdown()

    def reconnect(self):
        self.disconnect()
        self.connect()

    def flush(self, values):

        message = self.formatter(values)

        if self.sock == None:
            self.connect()
            return

        try:
            collectd.debug("%s.TcpWriter.flush: %s:%s %s" % ('$NAME', self.host, self.port, message))
            self.sock.send(message)
        except (TypeError, socket.error), msg:
            collectd.warning("%s error sending to host %s port %s: %s" % ('$NAME', self.host, self.port, msg))
            self.reconnect()
            
        
    def shutdown(self):
        collectd.debug("%s.%s.close()" % ('$NAME', self))
        try:
            self.sock.close()
        except socket.error:
            pass

    
    def __repr__(self):
        return "TcpWriter(host=%s, port=%s)" % (self.host, self.port)
