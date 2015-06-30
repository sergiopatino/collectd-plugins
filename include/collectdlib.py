# $__FILE__

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

