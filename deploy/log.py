import os
import utime
import sys

def log_exception(exception, fatal=True):
    timestamp = utime.localtime()
    timestamp_str = "{:04d}-{:02d}-{:02d} at: {:02d}:{:02d}:{:02d}".format(*timestamp[:6])
    
    log_string = ""
    if fatal:
        log_string += "Fatal Crash at: " + timestamp_str + "\n"
    else:
        log_string += "Non-Fatal Exception at: " + timestamp_str + "\n"
    log_string += "Sys print:\n"
    log_string += sys.print_exception(exception)
    log(log_string)

def log(log_string):
    log_folder = "/logs"
    log_file = "/logs/log.txt"
    archive_file = "/logs/log_old.txt"
    max_log_size = 1024 * 256  # 1/4 MB

    # Create the logs folder if it doesn't exist
    try:
        os.mkdir(log_folder)
    except OSError:
        pass

    # Check the log file size
    try:
        if os.stat(log_file)[6] > max_log_size:
            print("log_file too big... archiving...")
            archive_log(log_file, archive_file)
    except Exception as e:
        print("could not archive: ", e)
    
    timestamp = utime.localtime()
    timestamp_str = "{:04d}-{:02d}-{:02d}_{:02d}-{:02d}-{:02d}".format(*timestamp[:6])
    
    with open(log_file, "a") as log_file:
        log_file.write(timestamp_str +":\n" + log_string + "\n\n")

def read_log(filename="log.txt"):
    log_file_path = "/logs/" + filename
    try:
        with open(log_file_path, "rb") as log_file:
            while True:
                chunk = log_file.read(1024)  # Read 1KB at a time
                if not chunk:
                    break
                yield chunk
    except Exception as e:
        yield "Log file not found: " + str(e)

def list_archive():
    log_folder = "/logs"
    # List archived log files
    archived_files = [file for file in os.listdir(log_folder) if file.startswith("log_old")]
    return archived_files

def archive_log(log_file, archive_file):
    # Move the current log file to the archive file
    try:
        os.rename(log_file, archive_file)
    except Exception as e:
        print("could not archive log file: ", e)

def get_stack_trace():
    try:
        raise Exception("Getting stack trace")
    except Exception as e:
        stack_trace = ""
        for line in str(e).splitlines():
            stack_trace += "    " + line + "\n"
        return stack_trace
