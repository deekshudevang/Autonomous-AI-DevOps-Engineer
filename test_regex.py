import re

fault_buffer = []
is_faulting = False
ERROR_REGEX = re.compile(r'(\[ERROR\])|(Traceback \(most recent call last\):)|(ERROR)|(MemoryError)|(Exception)|(FATAL)')

logs = [
    "[ERROR] 2026-03-10 17:50:31",
    "Service: TaskService",
    "Error: Traceback (most recent call last):",
    '  File "/usr/local/lib/python3.11/site-packages/flask/app.py", line 1478, in __call__',
    "    return self.wsgi_app(environ, start_response)",
    "Exception: Fatal Server Crash: Memory overflow in handler",
    "[INFO] Should stop here"
]

for line in logs:
    if ERROR_REGEX.search(line):
        is_faulting = True
        fault_buffer.append(line.strip())
    elif is_faulting and (line.startswith(" ") or line.startswith("\t") or "Error" in line or "Service:" in line): 
        # Catch traceback lines or continuous error output
        fault_buffer.append(line.strip())
    else:
        if is_faulting:
            print("TRIGGERED!")
            print(fault_buffer)
            is_faulting = False
            fault_buffer = []
            break
