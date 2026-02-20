import os
import json
import record
from datetime import time, timedelta

def open_params(path : str) -> dict:
    with open(path, "r") as file:
        params = json.load(file)

        _prepare_duration = time.fromisoformat(params["prepare_duration"])
        return dict(
            start_time = time.fromisoformat(params["start_time"]),
            kill_time = time.fromisoformat(params["kill_time"]),
            prepare_duration = timedelta(
                minutes = _prepare_duration.minute, 
                seconds = _prepare_duration.second
            ),
            key_for_init = params["key_for_init"],
            exe_path = params["exe_path"],
            work_dir = os.path.dirname(params["exe_path"])
        )
    
def main():
    kwargs = open_params("params.json")
    record_scheduler = record.RecordScheduler(**kwargs)

    return record_scheduler.run()

if __name__ == "__main__":
    main()