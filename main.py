import ros_emb_interface
from ros_emb_interface import TopicTask

# Import all the necessary messages here (both ROS and proto messages)


# Thruster TopicTask

thruster_info = {"topic": "mov_motor_values",
                 "msg": None}

TopicTask(1, True, None, thruster_info)

# Create topic tasks here to link


if __name__ == "__main__":

    ros_emb_interface.run()
