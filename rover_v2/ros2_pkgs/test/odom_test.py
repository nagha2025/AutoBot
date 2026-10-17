#!/usr/bin/env python3

import lgpio
import time

PIN = 5

h = lgpio.gpiochip_open(4)

# claim as input with pullup
lgpio.gpio_claim_input(h, PIN, lgpio.SET_PULL_UP)

while True:
    val = lgpio.gpio_read(h, PIN)
    print(val)
    time.sleep(0.1)
