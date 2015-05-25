
# $__FILE__

import collectd
import socket

class UdpWriter(BaseWriter):
    """
    Send JSON inside UDP packet.

    :param formatter: Formatter instance.
    :param host: Host to send data to.
    :param port: 
    """

    def __init__(self, formatter, host, port, ttl=255, interface=None):
        collectd.debug("%s formatter=%s host=%s, port=%s ttl=%s interface=%s" % 
                       ('$NAME', formatter, host, port ,ttl, interface))

        super(UdpWriter, self).__init__(formatter)

        self.host = host
        self.port = int(port)
        self.interface = interface
        self.ttl = ttl


        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        if self.interface:
            # Crude test to distinguish between interface names and IP addresses.
            interface_ip = None
            try:
                if socket.gethostbyname(self.interface) == self.interface:
                    interface_ip = self.interface
            except socket.gaierror:
                try:
                    import netifaces
                    interface_ip = netifaces.ifaddresses(self.interface)[0]['addr']
                except (ImportError, OSError, ValueError), msg:
                    collectd.notice("%s error setting interface: %s" % ('$NAME', msg))

            if interface_ip:
                try:
                    self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(interface_ip))
                except socket.error, msg:
                    collectd.notice("%s error setting interface: %s" % ('$NAME', msg))
            else:
                # Fudge self.interface to make self.__repr__() look better
                self.interface = '<invalid>'
                

        if self.ttl:
            try:
                self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, self.ttl)
            except socket.error, msg:
                collectd.notice("%s error setting TTL to %d for host %s port %s: %s" % 
                                 ('$NAME', self.ttl, self.host, self.port, msg))
                # Fudge self.ttl to make self.__repr__() look better
                self.ttl = '<invalid>'


    def flush(self, values):
       
        message = self.formatter(values)

        try:
            collectd.debug("%s.UdpWriter.flush: %s:%s %s" % ('$NAME', self.host, self.port, message))
            self.sock.sendto(message, (self.host, self.port))
        except (TypeError, socket.error), msg:
            collectd.warning("%s error sending to host %s port %s: %s" %
                             ('$NAME', self.host, self.port, msg))

        
    def shutdown(self):
        collectd.debug("%s.%s.close()" % ('$NAME', self))
        try:
            self.sock.close()
        except socket.error:
            pass

    
    def __repr__(self):
        return "UdpWriter(host=%s, port=%s, interface=%s, ttl=%s, sock=%s)" % \
                (self.host, self.port, self.interface, self.ttl, self.sock)
