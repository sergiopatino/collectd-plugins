#!/bin/sh

for version in 5.4.2 5.4.1 5.4.0 5.3.2 5.3.0 5.2.2; do
#    version=`echo $c | sed 's;/opt/collectd-;;g'`

    echo ""
    echo "========= $version ================"
    echo ""
    sleep 5

    expect-lite VERSION=$version test.elt
    if [ $? -ne 0 ]; then
        exit 
    fi
done
