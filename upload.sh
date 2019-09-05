#!/bin/bash

export PYENV_ROOT="$HOME/.pyenv"

export PATH="$PYENV_ROOT/bin:$PATH"

CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

CURRENT_TIME="$(date -u)"

git -C $CURRENT_DIR checkout dev

eval "$(pyenv init -)" && pyenv shell sci && python $CURRENT_DIR/generate.py

git -C $CURRENT_DIR add proxy.json

git -C $CURRENT_DIR commit -m "$CURRENT_TIME"

git -C $CURRENT_DIR push origin dev



