# -*- coding: utf-8 -*-
# The MIT License
#
# Copyright (c) 2018 Aaron Greenyer
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""
    search_algorithms.py
    ~~~~~~~~~~~

    Creates a variable search method.

    :copyright: 2018 by Aaron Greenyer
    :license: MIT, see COPYING for more details.
"""

class SearchAlgorithm:
    def __init__(self, search_param):
        self.search_finished = False
        self.start = search_param.get('start', '0')
        self.stop = search_param.get('stop', '0')
        self.search_range = [self.start, self.stop]
        self.start_resolution = search_param.get('start_res', '1')
        self.final_resolution = search_param.get('final_res', '1')
        if self.start_resolution < self.final_resolution:
            self.start_resolution = self.final_resolution
        self.current_resolution = self.start_resolution
        self.step_reduction = search_param.get('step_reduction', '10')
        self.search_method = search_param.get('search_method', 'SINGLE').upper()
        self.over_run = search_param.get('over_run', '0')
        self.under_run = search_param.get('under_run', '0')
        self.repeat = search_param.get('repeat', '0')
        self.fail_limit = search_param.get('fail_limit', None)
        self.fail_count = 0
        self.control_value = None
        self.test_history = []
        self.search_index = 0
        self.fibonacci = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]

    def update_control_value(self):
        if self.search_method == 'SINGLE':
            self.control_value = self.start

        elif self.search_method == 'REPEAT':
            self.control_value = self.start

        elif self.search_method == 'SWEEP':
            self.control_value = self.start + (self.current_resolution * self.search_index)

        elif self.search_method == 'BINARY':
            if self.test_history:
                step_size = ((self.stop - self.start) / (2 ^ self.search_index))
                step_size = round(self.final_resolution * round(step_size / self.final_resolution), 10)
                step_size = (step_size, self.final_resolution)[step_size < self.final_resolution]
                self.control_value = self.control_value + (step_size, - step_size)[self.test_history[-1][1]]
            else:
                self.control_value = self.start

        elif self.search_method == 'FIBONACCI':
            if self.test_history:
                step_size = ((self.stop - self.start) / self.fibonacci[self.fail_count])
                step_size = round(self.final_resolution * round(step_size / self.final_resolution), 10)
                step_size = (step_size, self.final_resolution)[step_size < self.final_resolution]
                self.control_value = self.control_value + (step_size, - step_size)[self.test_history[-1][1]]
            else:
                self.control_value = self.start

        elif self.search_method == 'JUMP':
            if self.test_history:
                if self.test_history[-1][1]:
                    self.control_value = self.control_value + self.current_resolution
                else:
                    self.control_value = self.control_value - self.current_resolution
                    self.current_resolution = self.current_resolution / self.step_reduction
                    self.control_value = self.control_value + self.current_resolution
            else:
                self.control_value = self.start

        if self.control_value < self.start:
            self.control_value = self.start
        if self.control_value > self.stop:
            self.control_value = self.stop

        self.search_index += 1

        return self.control_value

    def search_finished(self, result_bool):
        # Aborting test
        self.test_history.append((self.control_value, result_bool)).sort()
        if result_bool == -1:
            self.search_finished = True
            return self.search_finished
        # if the result has failed, check conditions to see if the search should be cancelled.
        if not result_bool:
            if self.fail_limit is not None:
                self.fail_count += 1
                if self.fail_count >= self.fail_limit:
                    # cancel search if there have been too many failed results (normally for repeat tests).
                    self.search_finished = True
                    return self.search_finished
            elif self.control_value == self.start:
                # cancel test if the start value has failed.
                self.search_finished = True
                return self.search_finished
            elif self.current_resolution == self.final_resolution and self.control_value < self.search_range[0]:
                if self.under_run is not None:
                    if self.under_run <= self.search_range[0] - self.control_value:
                        # cancel test if the under_run value has failed, this might mean the test has an error
                        self.search_finished = True
                        return self.search_finished
                else:
                    self.search_finished = True
                    return self.search_finished
            elif self.current_resolution == self.final_resolution \
                    and (self.test_history[-1][1] or self.test_history[-2][1]):
                self.search_finished = True
                return self.search_finished
            else:
                # carry on searching
                pass
        else:
            if self.control_value == self.stop:
                self.search_finished = True
                return self.search_finished
            elif self.current_resolution == self.final_resolution and self.control_value > self.search_range[1]:
                if self.over_run is not None:
                    if self.over_run >= self.control_value - self.search_range[1]:
                        # cancel test if the over_run value has passed, this might mean the test has an error
                        self.search_finished = True
                        return self.search_finished
                else:
                    self.search_finished = True
                    return self.search_finished
