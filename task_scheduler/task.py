
from . import task_scheduler


class Task(object):
    """A task object used to schedule or execute an event.

    There are two types of tasks:

    - Tx tasks: These tasks will gather data (if there's any) from its
      callback and request the embedded device to perform an action with
      this data.

    - Rx tasks: These tasks will receive data (if there's any) and pass
      it to its callback to perform an action that was requested by the
      embedded device.
    """

    def __init__(self, task_id: int, is_rx: bool, msg_obj, callback=None):

        self.msg = msg_obj  # Protobuf Message object
        self.is_rx = is_rx  # Tells if task is receives a request or schedules one
        self.callback = callback  # Callback to handle task when invoked by the task scheduler
        self.id = task_id.to_bytes(1, "big")  # Register number for the task

        if task_scheduler.is_task_registered(task_id):
            raise KeyError(f"Task number '{task_id}' has already been registered.")
        elif is_rx:
            if callback is None:
                raise ValueError("There needs to be a callback set for rx tasks.")
            task_scheduler.register_task(task_id, self)

    def __repr__(self):

        return "Task {}".format(self.id)

    def alert_completion(self):
        """Alert other device the task has been completed when it was handled."""

        task_scheduler.pass_completion_message(self)

    def schedule(self):
        """Schedule task to be handled by the task scheduler."""

        task_scheduler.schedule_task(self)

    def was_not_handled(self):
        """Verify if task has been processed/handled by the task scheduler."""

        return task_scheduler.is_task_in_queue(self)
