import base64
import subprocess


def run_command(command):
    command = command.rstrip()  # trim the new line
    # run shell command and get the output back
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
    except Exception:
        output = "Failed to execute command. \r\n"

    return output

print( base64.b64encode("gosd"))