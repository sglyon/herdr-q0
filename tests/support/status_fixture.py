"""Plain terminal status fixture for manually testing native Herdr lifecycle events."""
import sys
import time
sys.stdout.write('\033]7501;state=idle:app=q0-test\033\\')
sys.stdout.flush()
time.sleep(120)
