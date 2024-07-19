#!/bin/bash

exec python3 contacts.py &
exec python3 mainnet_checking_loop.py &
exec python3 turing_checking_loop.py
