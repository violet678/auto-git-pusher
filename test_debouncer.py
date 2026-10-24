# test_debouncer.py
import time
from debouncer import Debouncer

calls = []
d = Debouncer(0.3, lambda: calls.append(time.time()))

for _ in range(10):       # 10 triggers rápidos
    d.trigger()
    time.sleep(0.05)

time.sleep(0.5)
assert len(calls) == 1, f"esperava 1, veio {len(calls)}"
print("ok")