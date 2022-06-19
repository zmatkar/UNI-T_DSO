#!/bin/bash

echo "Converting resource"
pyrcc5 UI/images.qrc -o UI/images_rc.py

echo "Converting ui file"
pyuic5 --from-imports UI/simpleUI.ui -o UI/simpleUI.py


