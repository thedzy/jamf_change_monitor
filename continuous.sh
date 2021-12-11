#!/bin/sh

# Kept for legacy reasons, however a daemon would be a wiser approach

# Run this for continual running of the code for faster alerts.
# Note: This will increase the strain on your API
#   Consider dedicating a node or increasing the performance of your nodes to accommodate is recommended

# The time to wait between runs in minutes
STAGGER_TIME=3

# Get path to the python script
BASE_DIR=$(dirname $0)

if [ "$1" == "--help" ]; then
    printf "Usage: continuous.sh [options]\n  Run jamf_change_monitor.py every %d minutes\n"  $STAGGER_TIME
   "$BASE_DIR/jamf_change_monitor.py" "${@}"
    exit 0
fi

# Run the python script in an indefinite loop passing parameters from scrip python
while true; do
  "$BASE_DIR/bin/python3" "$BASE_DIR/jamf_change_monitor.py" "${@}"
  sleep $(( STAGGER_TIME * 60 ))
done

exit