
__all__ = ["run",
           "init",
           "get_task",
           "is_task_registered"]


import serial
from time import time
from collections import deque
import serial.tools.list_ports as list_ports


# Task scheduler parts

_SER_CH = None  # Serial channel to receive and send data
_CH_OPEN_TIME = .2  # Time window to receive message (in seconds)
_TASK_RESET_TIME = 1  # Time window to resend task if not completed

_task_holder = {}  # Dictionary to store the created tasks
_prev_task = None  # Previously handled task
_start_time = None  # Time used to recall a task callback if the Arduino has not replied
_task_queue = deque()  # Queue to store the tasks


# Task scheduler interface methods

# TODO: Change to list_ports.grep instead of using _get_port
def init(baud_rate=9600, port_search="Arduino"):
    """Initialize task scheduler attributes at the start."""

    global _start_time, _SER_CH

    _SER_CH = serial.Serial(_get_port(port_search).device, baud_rate)
    _start_time = time()


def close():
    """Close the task scheduler."""

    _SER_CH.close()


def get_task(task_id):
    """Get a task by passing its task number if it's valid."""

    return _task_holder.get(task_id)


def is_task_in_queue(task):
    """Verify if the task is in the queue."""

    return task in _task_queue


def is_task_registered(task_id):
    """Checks if a task with the given task number was created."""

    return task_id in _task_holder


def pass_completion_message(task):
    """Passes the completion message to the tx message."""

    _transmit_message(task)


def register_task(task_id, task):
    """Register a task with the given number."""

    _task_holder[task_id] = task


def run():
    """Runs the task scheduler."""

    if _SER_CH.in_waiting:
        _handle_incoming_message()
    if _task_queue:
        _handle_current_task()


def schedule_task(task):
    """Schedule a task by putting it in the task queue."""

    if task not in _task_queue:
        _task_queue.append(task)


# Rx task handling methods

def _handle_incoming_message():
    """
    A receiver (rx) task specific method.

    This goes through different steps to process the incoming information
    from the rx serial channel of the rx message object and it ends this
    by routing the information that was received and clearing up the
    message.
    """

    task_id, proto_msg = _extract_message()
    _route_data(task_id, proto_msg)


def _route_data(task_id, msg_str):
    """Send the data to correct task and execute task's callback.

    It is assumed that when a message is not valid, the user wants to
    print information coming from the serial channel instead of triggering
    a task.

    This method also responds by removing
    """

    task = _task_holder.get(task_id)
    if task is not None:  # If rx task
        task.msg.ParseFromString(msg_str)
        task.callback()
        task.msg.Clear()
    elif len(_task_queue) != 0 and task_id == _task_queue[0].id[0]:  # If tx task in queue
        _task_queue.popleft()


# Tx handling methods

def _handle_current_task():
    """
    A transmitter (tx) task specific method.

    This sends the necessary information, so the Arduino can perform a
    certain task. It remains performing the same task until the task is
    removed from the first spot in the task queue.
    """

    global _start_time, _prev_task

    task = _task_queue[0]  # Grab first task in task queue
    is_prev_task = _prev_task == task  # Verify if current task was the previous one
    reset_task_timer = time() - _start_time > _TASK_RESET_TIME

    if (is_prev_task and reset_task_timer) or not is_prev_task:
        if task.callback is not None:
            task.callback()
        _transmit_message(task)
        task.msg.Clear()
        if reset_task_timer:
            _start_time = time()
        _prev_task = task  # This saves the current task for a later comparison


# Serial channel methods

def _extract_message():

    start = time()

    # Read incoming message from serial channel
    bin_msg = b''
    while _SER_CH.in_waiting and time() - start < _CH_OPEN_TIME:
        bin_msg += _SER_CH.read()

    task_id = bin_msg[0]  # Task id
    proto_msg = bin_msg[1:]  # Protocol buffer message

    return task_id, proto_msg


def _transmit_message(task):

    bin_msg = task.id + task.msg.SerializePartialToString()
    _SER_CH.write(bin_msg)


def _get_port(port_search):
    """Get the port for the Arduino"""

    # This is the same as using list_ports.grep but this only gives you one port
    for port in list_ports.comports():
        if port_search in port.description:
            return port
