#!/usr/bin/env python
from __future__ import print_function
from os import system

import rospy, time
from sensor_msgs.msg import Range

from teleop import Car


class CarState:

    def __init__(self, throttle, steering):
        self.throttle = throttle
        self.steering = steering

    def __str__(self):
        return 'thr=%s, str=%s' % (self.throttle, self.steering)

    def __repr__(self):
        return str(self)

class Behavior(object):

    def __init__(self, states, durations):
        t0 = time.time()
        self.starting_times = [t0]
        for d in durations:
            self.starting_times.append(self.starting_times[-1] + d)
        self.starting_times = self.starting_times[::-1]
        self.states = states[::-1]
        self.durations = durations
        self.finished = False

    def step(self, car):
        t = time.time()
        if len(self.starting_times) > 0 and t >= self.starting_times[-1]:
            self.starting_times.pop()
            if len(self.states) == 0:
                # print('    No more states to do, so finishing.')
                self.finished = True
            else:
                next_state = self.states.pop()
                # print('   Executing next state: %s.' % next_state)
                car.throttle = next_state.throttle
                car.steering = next_state.steering
        elif len(self.starting_times) == 0:
            # print('    No more times to pop, so finishing.')
            self.finished = True


class Evade(Behavior):

    def __init__(self, left=True):
        print('Beginning evasion behavior (left=%s).' % left)
        self.left = left
        REV = -.25
        durations_states = [
            [.5, CarState(REV, 0)],
            [2.5, CarState(REV, 1 if left else -1)],
            [.5, CarState(0, 0)]
        ]
        ss = [s for (d,s) in durations_states]
        ds = [d for (d,s) in durations_states]
        super(Evade, self).__init__(ss, ds)

class BumpDriver(object):

    def __init__(self):
        rospy.init_node('bump_driver')

        self.ranges = [20, 20]

        self.REACTION_RATE = 10
        self.BUMP_DISTANCE = 40.
        self.FORWARD_SPEED = .25

        rospy.Subscriber('sensors/ultrasound_0', Range, self.callback_left)
        rospy.Subscriber('sensors/ultrasound_1', Range, self.callback_right)

        self.car = Car()

        self.behavior = None

        self.loop()

    def callback_left(self, range_message):
        self.ranges[0] = range_message.range

    def callback_right(self, range_message):
        self.ranges[1] = range_message.range

    def test(self):
        self.car.steering = 1
        time.sleep(1)
        self.car.throttle = 1
        time.sleep(1)
        self.car.stop()
        time.sleep(4)

    def evade(self):
        self.behavior = Evade(left=self.ranges[0] > self.ranges[1])

    def go(self):
        self.behavior = None

    def loop(self):
        rate = rospy.Rate(self.REACTION_RATE)

        while not rospy.is_shutdown():

            if not isinstance(self.behavior, Evade):
                if min(self.ranges) < self.BUMP_DISTANCE:
                    print('dl=%.0f, dr=%.2f, dmin=%s' % (self.ranges[0], self.ranges[1], min(self.ranges),))
                    self.evade()
                elif min(self.ranges) >= self.BUMP_DISTANCE:
                    self.go()

            if self.behavior is None:
                self.car.steering = 0
                self.car.throttle = self.FORWARD_SPEED

            else:
                if self.behavior.finished:
                    print('"%s" behavior finished! Deleting.' % type(self.behavior).__name__)
                    self.behavior = None
                    self.go()
                else:
                    self.behavior.step(self.car)
            
            rate.sleep()


if __name__ == '__main__':
    BumpDriver()