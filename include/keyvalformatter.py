
# $__FILE__

def keyval_formatter(values_dict):

    collectd.debug('%s values_dict=%s' % ('$NAME', values_dict))

    format = 'time=%10.3f host="%s" plugin="%s" plugin_instance="%s" type="%s" type_instance="%s" interval=%d value=%f dsname="%s" dstype="%s" dsmin=%s dsmax=%s\n'
    message = ''

    for i,value in enumerate(values_dict['values']):

        message += format % (
                 values_dict['time'], values_dict['host'], values_dict['plugin'], values_dict['plugin_instance'],
                 values_dict['type'], values_dict['type_instance'], values_dict['interval'],
                 value, values_dict['dsname'][i], values_dict['dstype'][i], 
                 values_dict['dsmin'][i], values_dict['dsmax'][i])

    return message
