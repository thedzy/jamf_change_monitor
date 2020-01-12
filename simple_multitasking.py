#!/usr/bin/env python3

"""
Script:	simple_multitasking.py
Date:	2018-11-28
Platform: MacOS
Description:
Class to handle threading, getting its results and tracking if its been handled
https://docs.python.org/3.6/library/threading.html
"""
__author__ = 'thedzy'
__copyright__ = 'Copyright 2020, thedzy'
__license__ = 'GPL'
__version__ = '1.0'
__maintainer__ = 'thedzy'
__email__ = 'thedzy@hotmail.com'
__status__ = 'Development'

from threading import Thread
import threading
import time


class ThreadFunction(Thread):
    LIMIT = threading.Semaphore(25)

    def __init__(self, target, *args, **kwargs):
        args = [] if len(args) == 0 else args
        Thread.__init__(self, kwargs.get('group', None), target, kwargs.get('name', None), args, kwargs, daemon=None)

        self._return = None
        self._is_handled = False
        # Capture the start time for calculating the run time
        self._start_time = time.time()
        self._end_time = 0

    def run(self):
        """
        Called when .start is triggered
        Starts the function
        :return: Self
        """
        self.LIMIT.acquire()
        self._return = self._target(*self._args, **self._kwargs)
        # Calculate the runtime
        self._end_time = time.time()
        return self

    def get_value(self):
        """
        Get the return value(s) from the function
        :return: Return Value (any)
        """
        Thread.join(self)
        self._is_handled = True
        self.LIMIT.release()
        return self._return

    def get_time(self):
        """
        Get the total run time of the function
        :return: Seconds (int)
        """
        return int(self._end_time - self._start_time)

    def is_handled(self):
        """
        Check whether the value(s) has retrieved from this function
        :return: (bool)
        """
        return self._is_handled

print('Not intendedt o run on independantly')
