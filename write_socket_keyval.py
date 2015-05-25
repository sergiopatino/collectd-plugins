# The MIT License (MIT)
# 
# Copyright (c) 2015 Markus Juenemann
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


# include/collectdlib.py

import collectd
import re

DEBUG = False


def values_to_dict(values):
    """
    Convert `collectd.Values` instance to dictionary.

    :param values: Instance of `collectd.Values`.
    :returns: Dictionary representing `collectd.Values`.

    """

    assert isinstance(values, collectd.Values)
 
    values_dict = {'time': values.time,
                   'interval': values.interval,
                   'host': values.host,
                   'plugin': values.plugin,
                   'plugin_instance': values.plugin_instance,
                   'type': values.type,
                   'type_instance': values.type_instance,
                   'values': values.values}

    try:
        values_dict['dsname'] = values.dsname
    except AttributeError:
        values_dict['dsname'] = []
    
    try:
        values_dict['dstype'] = values.dstype
    except AttributeError:
        values_dict['dstype'] = []
    
    try:
        values_dict['dsmin'] = values.dsmin
    except AttributeError:
        values_dict['dsmin'] = []
    
    try:
        values_dict['dsmax'] = values.dsmax
    except AttributeError:
        values_dict['dsmax'] = []

    return values_dict


def add_typesdb_info_to_values(values_dict, types_dict=dict()):
    """
    Add information from types.db files.

    :param values_dict: Dictionary.
    :param types_dict: A dictionary containing information from
        Collectd's types.db files in the same format as returned
        by `read_types_db`. If this argument is omitted only
        information that can be obtained by calling `collectd.get_dataset()`
        is used.
    :returns: `collectd.Values` with additional attributes.

    Since Collectd 5.5 the Python plugin provides a `get_dataset()`
    function that returns information from the types.db files. In this 
    case `types_dict` does not have to be passed to 
    `add_typesdb_info_to_values()`. The Python plugin of earlier 
    Collectd versions does not provide `get_dataset()` and it is
    necessary to read (ideally all) types.db by calling
    `read_typesdb(path)` for each file (updating the dictionary
    with each call) and passing the resulting dictionary as
    and argument to `add_typesdb_info_to_values()`.

    """

    values_dict['dsname'] = []
    values_dict['dstype'] = []
    values_dict['dsmin'] = []
    values_dict['dsmax'] = []


    dataset = None
    try:
        dataset = collectd.get_dataset(values_dict['type'])
    except AttributeError:
        #
        # collectd.get_dataset() is not yet implemented. Try to get
        # the nformation from TYPES which holds the information
        # we read from types.db files.
        #
        try:
            dataset = types_dict[values_dict['type']]
        except KeyError:
            pass
    except TypeError, msg:
        pass


    if dataset:
        for (i, value) in enumerate(values_dict['values']):
            (dsname, dstype, dsmin, dsmax) = dataset[i]
            values_dict['dsname'].append(dsname)
            values_dict['dstype'].append(dstype)
            values_dict['dsmin'].append(dsmin)
            values_dict['dsmax'].append(dsmax)

    return values_dict


def read_typesdb(path):
    """    
    Read a Collectd types.db file.

    :param path: Path to types.db file.
    :returns: Dictionary where the keys are the "type" and values
        are list of ```(dsname, dstype, dsmin, dsmax)``` tuples.
        If ```dsmin``` or ```dsmax``` are returned as floats or
        as the character ```U``` if undefined.

    This function should be called for each types.db file,
    updating the dictionary each time.

    >>> types_dict = {}
    >>> types_dict.update('/usr/share/collectd/types.db')
    >>> types_dict.update('/usr/local/share/collectd/types.db')

    Since Collect 5.5 the Python plugin implements `collectd.get_dataset()`
    and `read_typesdb()` is no longer required.

    """

    types_dict = {}

    try:
        with open(path) as fp:
            for line in fp:
                fields = re.split(r'[,\s]+', line.strip())

                # Skip comments
                if fields[0].startswith('#'):
                    continue

                name = fields[0]

                if len(fields) < 2:
                    collectd.notice("configuration error: %s in %s is missing definition" % (name, path))
                    continue

                name = fields[0]

                types_dict[name] = []

                for field in fields[1:]:
                    fields2 = field.split(':')

                    if len(fields2) < 4:
                        collectd.notice("configuration error: %s %s has wrong format" % (name, field))
                        continue

                    dsname = fields2[0]
                    dstype = fields2[1].lower()
                    dsmin  = fields2[2]
                    dsmax  = fields2[3]

                    if dsmin != 'U':
                        dsmin = float(fields2[2])

                    if dsmax != 'U':
                        dsmax = float(fields2[3])

                    types_dict[name].append((dsname, dstype, dsmin, dsmax))

                collectd.debug("read_types_db: types_dict[%s]=%s" % (name, types_dict[name]))

    except IOError, msg:
        collectd.notice("configuration error: %s - %s" % (path, msg))

    return types_dict



# include/keyvalformatter.py

def keyval_formatter(values_dict):

    collectd.debug('%s values_dict=%s' % ('write_socket_keyval', values_dict))

    format = 'time=%10.3f host="%s" plugin="%s" plugin_instance="%s" type="%s" type_instance="%s" interval=%d value=%f dsname="%s" dstype="%s" dsmin=%s dsmax=%s\n'
    message = ''

    for i,value in enumerate(values_dict['values']):

        message += format % (
                 values_dict['time'], values_dict['host'], values_dict['plugin'], values_dict['plugin_instance'],
                 values_dict['type'], values_dict['type_instance'], values_dict['interval'],
                 value, values_dict['dsname'][i], values_dict['dstype'][i], 
                 values_dict['dsmin'][i], values_dict['dsmax'][i])

    return message


# include/socketwriter.py

# include/_basewriter.py

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
        collectd.debug('%s.write_callback: values_object=%s' % ('write_socket_keyval', values_dict))

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

# include/_udpwriter.py

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
                       ('write_socket_keyval', formatter, host, port ,ttl, interface))

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
                    collectd.notice("%s error setting interface: %s" % ('write_socket_keyval', msg))

            if interface_ip:
                try:
                    self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(interface_ip))
                except socket.error, msg:
                    collectd.notice("%s error setting interface: %s" % ('write_socket_keyval', msg))
            else:
                # Fudge self.interface to make self.__repr__() look better
                self.interface = '<invalid>'
                

        if self.ttl:
            try:
                self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, self.ttl)
            except socket.error, msg:
                collectd.notice("%s error setting TTL to %d for host %s port %s: %s" % 
                                 ('write_socket_keyval', self.ttl, self.host, self.port, msg))
                # Fudge self.ttl to make self.__repr__() look better
                self.ttl = '<invalid>'


    def flush(self, values):
       
        message = self.formatter(values)

        try:
            collectd.debug("%s.UdpWriter.flush: %s:%s %s" % ('write_socket_keyval', self.host, self.port, message))
            self.sock.sendto(message, (self.host, self.port))
        except (TypeError, socket.error), msg:
            collectd.warning("%s error sending to host %s port %s: %s" %
                             ('write_socket_keyval', self.host, self.port, msg))

        
    def shutdown(self):
        collectd.debug("%s.%s.close()" % ('write_socket_keyval', self))
        try:
            self.sock.close()
        except socket.error:
            pass

    
    def __repr__(self):
        return "UdpWriter(host=%s, port=%s, interface=%s, ttl=%s, sock=%s)" %                 (self.host, self.port, self.interface, self.ttl, self.sock)


# include/callbacks.py

import collectd
import threading

WRITERS = []
TYPES_DICT = {}
LOCK = threading.Lock()

def configure_callback(config):

    global WRITERS
    global TYPES_DICT

    for node in config.children:
        key = node.key.lower()

        collectd.debug("%s key=%s node.values=%s" % ('write_socket_keyval', key, node.values))

        if key == 'typesdb':
            TYPES_DICT.update(read_typesdb(node.values[0]))
        elif key == 'udp':
            WRITERS.append(UdpWriter(keyval_formatter, *node.values))
        else:
            collectd.notice("%s configuration error: unknown key %s" % ('write_socket_keyval', key))


def init_callback(*args):
    """
    Start all writer threads.
    """

    for writer in WRITERS:
        writer.daemon = True
        writer.start()


def shutdown_callback():
    for writer in WRITERS:
        writer.shutdown()


def write_callback(values):
    """
    Pass values_object to all `WRITERS`.

    :param values: Instance of `collectd.Values`.

    An example of `values` is shown below. It may also contain `plugin_instance`
    and `type_instance` attributes. The `dsname`, `dstype`, `dsmin` and
    `dsmax` fields are are not present in `collectd.Values`. They are
    added in the `BaseFormatter.convert_values_to_dict()` method if possible.

      collectd.Values(type='load', plugin='load', host='localhost', time=1432083347.3517618,
                      interval=300.0, values=[0.0, 0.01, 0.050000000000000003])

    """

    collectd.debug('%s.write_callback: values_object=%s' % ('write_socket_keyval', values))


    # Add dataset from types.db files.
    #
    values_dict = add_typesdb_info_to_values(values_to_dict(values), TYPES_DICT)

    with LOCK:
        for writer in WRITERS:
            writer.write(values_dict)


# Register callbacks
#
collectd.register_config(configure_callback)
collectd.register_shutdown(shutdown_callback)
collectd.register_write(write_callback)
collectd.register_init(init_callback)