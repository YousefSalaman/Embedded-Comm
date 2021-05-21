
__all__ = ["run",
           "TopicTask"]


import rospy

import task_scheduler


# Translate to python 2 later

class TopicTask(task_scheduler.Task):
    """Helper class to create and connect the task scheduler and ROS.

    This class binds a ROS topic to a specific callback in the Arduino by
    using the task scheduler interface through Task class. By doing this,
    any part of the code can communicate to the Embedded system through a
    ROS topic and this will be translated to the Protocol Buffer API.

    The only requirement for this class is that a TopicTask object must
    have a counterpart in the Arduino, so the task scheduler can transfer
    values between the AUV's computer and the Arduino.
    """

    def __init__(self, task_id: int, send_data: bool, msg_obj, ros_info: dict):

        super().__init__(task_id, send_data, msg_obj)

        self.ros_msg = ros_info["msg"]  # Save the ros message class for later usage
        if send_data:
            self.ros_obj = rospy.Subscriber(ros_info["topic"],
                                            ros_info["msg"],
                                            self.tx_callback)
        else:
            self.callback = self.rx_callback
            self.ros_obj = rospy.Publisher(ros_info["topic"],
                                           ros_info["msg"])

    def rx_callback(self, proto_msg):
        """Callback to pass sensor values to the AUV's main computer.

        When this triggers through the task scheduler mechanism, this will pass
        on the protocol buffer message values to a ROS message and publish it,
        so the subscribers can receive the values.
        """

        ros_msg = self.ros_msg()  # Create ROS message object to publish

        # Pass value from protobuff message to ROS message
        for field in self.msg.DESCRIPTOR.fields_by_name:
            setattr(ros_msg, field, getattr(proto_msg, field))

        self.ros_obj.publish(ros_msg)
        self.alert_completion()  # Alert Arduino the values have been passed

    def tx_callback(self, ros_msg):
        """Callback to pass actuator/manipulator values to the Arduino.

        When this triggers through the ROS mechanism when a topic is updated,
        this will pass on the ROS message values to the stored protocol buffer
        message and then schedule a task to update the values in the Arduino.
        """

        # Pass values from the ROS message to the protobuff message
        for field in self.msg.DESCRIPTOR.fields_by_name:
            setattr(self.msg, field, getattr(ros_msg, field))

        self.schedule()  # Pass values to Arduino


def run(baud_rate=9600, port_search="Arduino"):
    """Runs the ROS/Embedded interface."""

    # Initialize the ROS/Embedded interface
    rospy.init_node("embedded interface")
    task_scheduler.init(baud_rate, port_search)

    # Run task scheduler along with ROS
    while not rospy.is_shutdown():
        task_scheduler.run()

    task_scheduler.close()  # Terminate task scheduler
