#!/usr/bin/python3

import rclpy
from rclpy.node import Node

from geometry_msgs.msg import Twist, Accel, Wrench

#ubuntu@uwbot-14:~$ cat /opt/ros/galactic/share/geometry_msgs/msg/Wrench.msg
## This represents force in free space, separated into its linear and angular parts.
#
#Vector3  force
#Vector3  torque
#ubuntu@uwbot-14:~$ cat /opt/ros/galactic/share/geometry_msgs/msg/Accel.msg
## This expresses acceleration in free space broken into its linear and angular parts.
#Vector3  linear
#Vector3  angular




class MinimalPublisher(Node):
    def __init__(self):
        super().__init__('minimal_publisher')
        self.publisher_ = self.create_publisher(Twist, '/cmd_vel', 1)

        import rclpy.qos
        import rclpy.time
        from copy import copy
        qos_profile_sensor_data = copy(rclpy.qos.qos_profile_sensor_data)
        qos_policy = copy(rclpy.qos.qos_profile_sensor_data)

        self.cmd_acc_subscription = self.create_subscription(
                Accel,
                '/cmd_acc',
                self.cmd_acc_listener_callback,
                qos_profile_sensor_data)
        self.cmd_acc_subscription  # prevent unused variable warning
        self.cmd_wrench_subscription = self.create_subscription(
                Accel,
                '/cmd_wrench',
                self.cmd_wrench_listener_callback,
                qos_profile_sensor_data)
        self.cmd_wrench_subscription  # prevent unused variable warning
        # TODO: cmd_wheel_trq

        self.msg_out =  Twist()
        self.msg_out.linear.x = 0.
        self.msg_out.linear.y = 0.
        self.msg_out.linear.z = 0.
        self.msg_out.angular.x = 0.
        self.msg_out.angular.y = 0.
        self.msg_out.angular.z = 0.
        self.vel_tolerance = 1e-3
        self.zero_command = 0
        self.msg_out_limits = Twist()
        self.msg_out_limits.linear.x = 0.3
        self.msg_out_limits.angular.x = 0.1

        self.timer_period = 0.05
        self.state = "off"
        self.timer = self.create_timer(self.timer_period, self.timer_callback)
        
        self.command_state = "off"
        self.last_command = self.get_clock().now() - rclpy.time.Duration(seconds=1.0)
        self.get_logger().info("Virtual Model ready")

    def cmd_acc_listener_callback(self, msg):
        self.last_command = self.get_clock().now()
        self.cmd_acc_msg = msg
        self.msg_out.linear.x = self.msg_out.linear.x + \
            self.cmd_acc_msg.linear.x * self.timer_period
        self.msg_out.angular.z = self.msg_out.angular.z + \
            self.cmd_acc_msg.angular.z * self.timer_period
        # saturate output
        self.msg_out.linear.x = min( self.msg_out_limits.linear.x, self.msg_out.linear.x)
        self.msg_out.linear.x = max(-self.msg_out_limits.linear.x, self.msg_out.linear.x)
        self.msg_out.angular.z = min( self.msg_out_limits.angular.z, self.msg_out.angular.z)
        self.msg_out.angular.z = max(-self.msg_out_limits.angular.z, self.msg_out.angular.z)
        
        self.get_logger().info('Publishing: %2.2f / %2.2f' % (self.msg_out.linear.x,self.msg_out.angular.z))
        self.publisher_.publish(self.msg_out)
        self.state = "acc"

    def cmd_wrench_listener_callback(self, msg):
        self.cmd_wrench_msg = msg
        self.last_command = self.get_clock().now()
        self.state = "wrench"
        self.msg_out.linear.x = self.msg_out.linear.x + \
            self.cmd_wrench_msg.linear.x * self.timer_period / self.linear_inertia
        self.msg_out.angular.z = self.msg_out.angular.z + \
            self.cmd_acc_msg.angular.z * self.timer_period / self.angular_inertia
        # saturate output
        self.msg_out.linear.x = min( self.msg_out_limits.linear.x, self.msg_out.linear.x)
        self.msg_out.linear.x = max(-self.msg_out_limits.linear.x, self.msg_out.linear.x)
        self.msg_out.angular.z = min( self.msg_out_limits.angular.z, self.msg_out.angular.z)
        self.msg_out.angular.z = max(-self.msg_out_limits.angular.z, self.msg_out.angular.z)

    def timer_callback(self):
        if (self.get_clock().now() - self.last_command) < rclpy.time.Duration(seconds=0.1):
            self.command_state = "active"
        elif self.command_state == "active":
            self.get_logger().info('Lost publisher, cmd_vel = 0.00 / 0.00')
            self.msg_out.linear.x = 0.
            self.msg_out.angular.z = 0.
            self.publisher_.publish(self.msg_out)
            self.command_state = "off"
        
        



def main(args=None):
    rclpy.init(args=args)
    minimal_publisher = MinimalPublisher()

    rclpy.spin(minimal_publisher)

    minimal_publisher.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()





