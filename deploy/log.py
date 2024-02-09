import os
import utime
import sys

def log_exception(exception, fatal = True):
    log_folder = "/logs"
    log_file = "/logs/error_log.txt"
    max_log_size = 1024 * 1024  # 1 MB

    # Create the logs folder if it doesn't exist
    try:
        os.mkdir(log_folder)
    except OSError:
        pass

    # Check the log file size
    try:
        if os.stat(log_file)[1] > max_log_size:
            archive_log(log_folder)
    except Exception as e:
        print("could not archive: ", e)

    timestamp = utime.localtime()
    timestamp_str = "{:04d}-{:02d}-{:02d} at: {:02d}:{:02d}:{:02d}".format(*timestamp[:6])
    with open(log_file, "a") as log_file:
        # Write exception information to the log file
        if fatal: log_file.write("Fatal Crash at: " + timestamp_str + "\n")
        else: log_file.write("Non-Fatal Exception at: " + timestamp_str + "\n")
        log_file.write("Sys print:\n")
        sys.print_exception(exception, log_file)
        log_file.write("\n\n")

def read_log(filename="error_log.txt"):
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
    archived_files = [file for file in os.listdir(log_folder) if file.startswith("error_log_archive_")]
    return archived_files

def archive_log(log_folder = "/logs"):
    log_file = "/logs/error_log.txt"
    timestamp = utime.localtime()
    timestamp_str = "{:04d}-{:02d}-{:02d}_{:02d}-{:02d}-{:02d}".format(*timestamp[:6])
    archive_file = "/logs/error_log_archive_{}.txt".format(timestamp_str)

    # Move the current log file to an archive file with timestamp
    try:
        os.rename(log_file, archive_file)
        # Create a new empty log file
        open(log_file, 'w').close()
    except Exception as e:
        print("could not rename file for some reason: ", e)

def get_stack_trace():
    try:
        raise Exception("Getting stack trace")
    except Exception as e:
        stack_trace = ""
        for line in str(e).splitlines():
            stack_trace += "    " + line + "\n"
        return stack_trace