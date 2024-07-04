#!/bin/bash

exec python3 main_checkpoint.py &
exec python3 main_listener.py &
exec python3 main_validator.py
