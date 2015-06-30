
# $__FILE__

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

        collectd.debug("%s key=%s node.values=%s" % ('$NAME', key, node.values))

        if key == 'typesdb':
            TYPES_DICT.update(read_typesdb(node.values[0]))
#if "$WRITER" eq "socket"
        elif key == 'udp':
            WRITERS.append(UdpWriter($FORMAT_formatter, *node.values))
        elif key == 'tcp':
            WRITERS.append(TcpWriter($FORMAT_formatter, *node.values))
#        elif key == 'unix':
#            WRITERS.append(UnixWriter($FORMAT_formatter, *node.values))
#endif
        else:
            collectd.notice("%s configuration error: unknown key %s" % ('$NAME', key))


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

    collectd.debug('%s.write_callback: values_object=%s' % ('$NAME', values))


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
