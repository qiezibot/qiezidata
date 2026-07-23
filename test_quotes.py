import subprocess, sys
result = subprocess.run([sys.executable, '-c', """
import py_compile
py_compile.compile("railway_file_server.py", doraise=True)
print("Syntax OK")
"""], capture_output=True, text=True, timeout=10)
print('STDOUT:', result.stdout)
print('STDERR:', result.stderr)
print('Return:', result.returncode)
