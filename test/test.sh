#!/bin/sh

for c in /opt/collectd-*; do
    version=`echo $c | sed 's;/opt/collectd-;;g'`
    echo "========= $VERSION ================"
    expect-lite VERSION=$version test.elt
done
