import collections
import operator
import random
import time
import math

class Task():

    def __init__(self, id, W, r_min, r_max, successor_ids):
        self.id = id
        self.W = W
        self.r_min = r_min
        self.r_max = r_max
        if self.W == 0:
            self.d_max = 0
            self.d_min = 0
        else: 
            self.d_max = math.ceil(self.W/self.r_min)
            self.d_min = math.ceil(self.W/self.r_max)
        self.successor_ids = successor_ids
        self.successors = {}
        self.predecessor_ids = []
        self.predecessors = {}
        
    def set_successors(self, tasks):
        for successor_id in self.successor_ids:
            self.successors[successor_id] = tasks[successor_id]

    def set_predecessors(self, tasks):
        self.find_predecessor_ids(tasks)
        for predecessor_id in self.predecessor_ids:
            self.predecessors[predecessor_id] = tasks[predecessor_id]

    def find_predecessor_ids(self, tasks):
        for task in tasks.values():
            for successor_id in task.successors:
                if successor_id == self.id:
                    self.predecessor_ids.append(task.id)

class Project():

    def __init__(self, name, tasks, R_max, l):
        self.name = name
        self.R_max = R_max 
        self.l = l
        self.tasks = tasks
        self.set_task_successors()
        self.set_task_predecessors()

    def set_task_successors(self):
        for task in self.tasks.values():
            task.set_successors(self.tasks)

    def set_task_predecessors(self):
        for task in self.tasks.values():
            task.set_predecessors(self.tasks)

    def get_heuristic_schedule(self):
        priority_scores = self.get_priority_scores(priority_rule = "LPF")
        sorted_by_priority_scores = [0]
        sorted_by_priority_scores.extend([x[0] for x in sorted(list(priority_scores.items())[1:len(self.tasks)-1], key=operator.itemgetter(1), reverse = True)])
        sorted_by_priority_scores.append(len(self.tasks)-1)
        activity_list_representation = {task_id:self.tasks[task_id] for task_id in sorted_by_priority_scores}
        print("alr=", [task.id for task in activity_list_representation.values()])
        schedule = self.serial_scheduling_scheme(activity_list_representation) 
        return schedule

    def get_priority_scores(self, priority_rule="LPF"):
        priority_scores = {}
        reverse_topological_order = self.topological_ordering(reverse=True)
        for task in reverse_topological_order:
            if len(task.successor_ids) == 0:
                priority_scores[task.id] = 0
            else:
                if priority_rule == "LPF":
                    priority_scores[task.id] = task.d_min + max(priority_scores[j] for j in task.successor_ids)
                elif priority_rule == "MWR":
                    priority_scores[task.id] = task.W + max(priority_scores[j] for j in task.successor_ids)
        return priority_scores

    def serial_scheduling_scheme(self, activity_list_representation):
        schedule = Schedule(self, activity_list_representation)
        for task in activity_list_representation.values():
            task_start = schedule.find_latest_predecessor_finish_time(task)
            schedule.greedily_schedule_task(task, task_start)
        return schedule

    def topological_ordering(self, reverse=False):
        ordered_tasks = []
        visited = [False]*len(self.tasks)
        for task in self.tasks.values():
            if visited[task.id] == False:
                self.topological_order_task(task, visited, ordered_tasks)
        if reverse == False:
            return(ordered_tasks)
        else:
            return(list(reversed(ordered_tasks)))

    def topological_order_task(self, task, visited, ordered_tasks):
        visited[task.id] = True
        for successor in task.successors.values():
            if visited[successor.id] == False:
                self.topological_order_task(successor, visited, ordered_tasks)
        ordered_tasks.insert(0, task)


class Schedule():

    def __init__(self, project, alr):
        self.alr = alr
        self.task_starts = {}
        self.task_ends = {}
        self.task_resource_usage = {}
        self.task_resource_usage_changes = {}
        self.l = project.l
        self.resource_availability = {0:project.R_max}

    def greedily_schedule_task(self, task, t):
        self.task_resource_usage[task.id] = collections.OrderedDict()
        self.task_resource_usage_changes[task.id] = []
        resource_available = self.resource_available_test(task, t) #enough resource available?
        if resource_available == False:
            #print("There was not enough resource to start task %d at time %f." %(task.id, t))
            t = self.get_next_event_time(t)
            self.greedily_schedule_task(task, t)
        else:
            self.task_starts[task.id] = t
            #print("Task %d started at time %f." %(task.id, t))
            resource_applied = self.get_resource_applied(task, t)
            self.add_task(task, t, resource_applied)

    def add_task(self, task, t, resource_applied):
        if self.task_resource_usage[task.id] == {} or resource_applied != list(self.task_resource_usage[task.id].items())[-1][1]:
            self.task_resource_usage_changes[task.id].append(t)
        next_event_time = self.get_next_event_time(t)
        if resource_applied == task.r_max:
            duration = task.d_min
        else:
            duration = task.W/resource_applied
        self.resource_availability[t] -= resource_applied
        task_finish = t + duration
        if next_event_time == None or next_event_time > task_finish: #if task finish before next event, i.e. resource availability at other events is not affected, task completed in this block
            self.resource_availability[task_finish] = self.resource_availability[t] + resource_applied########################## ive changed this but think this is correct
            self.resource_availability = dict(collections.OrderedDict(sorted(self.resource_availability.items())))
            self.task_resource_usage[task.id][task_finish] = 0
            self.makespan = task_finish
            self.task_ends[task.id] = task_finish
            self.task_resource_usage[task.id][t] = resource_applied
            self.task_resource_usage[task.id] = dict(collections.OrderedDict(sorted(self.task_resource_usage[task.id].items())))
        elif next_event_time == task_finish:
            self.task_resource_usage[task.id][task_finish] = 0
            self.makespan = task_finish
            self.task_ends[task.id] = task_finish
            self.task_resource_usage[task.id][t] = resource_applied
            self.task_resource_usage[task.id] = dict(collections.OrderedDict(sorted(self.task_resource_usage[task.id].items())))
        else: #if task finishes after next event, i.e. resource availability at other events is affected
            self.task_resource_usage[task.id][t] = resource_applied
            self.task_resource_usage[task.id] = (collections.OrderedDict(sorted(self.task_resource_usage[task.id].items())))
            remaining_area = task.W - (next_event_time - t)*resource_applied
            task_remaining = Task(task.id, remaining_area, min(task.r_min, remaining_area), task.r_max, task.successor_ids)
            resource_applied = self.get_resource_applied(task_remaining, next_event_time)
            self.add_task(task_remaining, next_event_time, resource_applied)
            task_finish = self.task_ends[task.id] #task finish was found in a deeper version of add_task

    def resource_available_test(self, task, t): #returns True if enough resource is available to start task at time t, otherwise returns False
        area = 0
        for event_time in self.resource_availability:
            if event_time >= t:
                resource_applied = self.get_resource_applied(task, event_time)
                if resource_applied < task.r_min:
                    break
                else:
                    next_event_time = self.get_next_event_time(event_time)
                    if next_event_time == None:
                        return True
                    else:
                        area += resource_applied*(next_event_time - event_time)
        if area >= task.W:
            return True
        else:
            return False

    def get_resource_applied(self, task, t): #returns greedy resource allocation to task at time t
        time_since_resource_change = self.get_time_since_resource_change(task, t)
        if time_since_resource_change < self.l: #if min. block not satisied, continue with current block
            print("min. block length has not been satisfied")
            resource_applied = list(self.task_resource_usage[task.id].items())[-1][1]
        else: #There is a better way of writing this function from here
            if self.resource_availability[t] > task.r_max:
                resource_applied = task.r_max
                duration = task.d_min
                if duration < self.l: #check that the amount of resource applied is meaning that min. block length is not satisfied, i.e. task is being completed too quickly 
                    resource_applied = task.W/self.l
            else:
                resource_applied = self.resource_availability[t]
                duration = math.ceil(task.W/resource_applied)
                if duration < self.l: #check that the amount of resource applied is meaning that min. block length is not satisfied, i.e. task is being completed too quickly
                    resource_applied = task.W/self.l
            #is it better to keep the same resource allocation?
            if resource_applied != 0:
                actual_duration = math.ceil(task.W/resource_applied)
                if len(self.task_resource_usage[task.id]) != 0:
                    if list(self.task_resource_usage[task.id].items())[-1][1] <= self.resource_availability[t]:
                        if actual_duration > task.W/list(self.task_resource_usage[task.id].items())[-1][1]: #if duration is shorter if resource allocation is kept constant
                            resource_applied = list(self.task_resource_usage[task.id].items())[-1][1]
        return resource_applied

    def get_time_since_resource_change(self, task, t): #returns last change in resource allocation to task 
        if self.task_resource_usage_changes[task.id] == []:
            time_since_resource_change = 1000000
        else:
            time_since_resource_change = t - self.task_resource_usage_changes[task.id][-1]
        return time_since_resource_change

    def get_next_event_time(self, event_time):
        event_times = list(self.resource_availability.keys())
        if event_time > max(event_times):
            return None
        else:
            for e in event_times:
                if e > event_time:
                    next_event_time = e
                    return next_event_time

    def find_latest_predecessor_finish_time(self, task):
        predecessor_finish_times = []
        for predecessor in task.predecessors.values():
            predecessor_finish_times.append(self.task_ends[predecessor.id])
        latest_predecessor_finish_time = max(predecessor_finish_times, default = 0)
        return latest_predecessor_finish_time
