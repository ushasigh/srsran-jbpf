#!/bin/bash
## Copyright (c) Microsoft Corporation. All rights reserved.
# shellcheck disable=SC1091

HERE="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd)"

pushd . > /dev/null > /dev/null
cd "$HERE" || exit 1

source ../set_vars.sh

if [ ! -d ".venv" ]; then
    echo "Creating virtualenv."
    ./init_venv.sh
fi

source .venv/bin/activate

python3 add_stream_ids.py -i $1 -o $2

ret=$?

deactivate

popd > /dev/null  > /dev/null || exit 1

exit $ret