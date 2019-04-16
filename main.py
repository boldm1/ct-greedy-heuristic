import task_project_schedule as tps
import os
import re

def load_tasks(stripped_lines, n_act, n_res):
    tasks = {}
    for activity in range(n_act):
        line_1 = stripped_lines[activity+1]
        line_2 = stripped_lines[n_act+activity+1]
        task_id = int(line_1[0])
        n_succ = int(line_1[2]) #number of successors
        succ_ids = []
        if n_succ > 0:
            for i in range(n_succ):
                succ_ids.append(int(line_1[3+i]))
        w = int(line_2[3]) #principle work-content
        u_lower, u_upper = [], []
        for r in range(n_res):
            u_lower.append(int(line_2[4+2*r]))
            u_upper.append(int(line_2[4+2*r+1]))
        task = tps.Task(task_id, w, u_lower[0], u_upper[0], succ_ids)
        tasks[task_id] = task
    return tasks

def load_project(project_file_path):
    f = open(project_file_path, 'r')
    raw_lines = f.read().splitlines()
    stripped_lines = []
    for line in raw_lines:
        stripped_lines.append(re.split('\t', line))
    first_line = stripped_lines[0]
    n_act = int(first_line[0])+2 #total number of activities incl. dummies
    n_res = int(first_line[1])
    last_line = stripped_lines[2*n_act + 1]
    b = [] #resource availabilities
    for r in range(n_res):
        b.append(int(last_line[r]))
    l = int(last_line[n_res]) #min. block length
    tasks = load_tasks(stripped_lines, n_act, n_res)
    project = tps.Project(project_file_path, tasks, b[0], l) #min block length has been removed
    return project

project_file_path = "test_instance.sch"

project = load_project(project_file_path)

schedules = project.get_heuristic_schedules()
print("schedule makespans: ", [schedule.makespan for schedule in schedules])
best_schedule = schedules[0]
print("l: ", project.l)
print("w: ", project.R_max)
print("resource_availability: ", best_schedule.resource_availability)
print("task_resource_usages: ", best_schedule.task_resource_usage)
print("optimal makespan: ", max(best_schedule.resource_availability.keys()))
print("optimal activity list representation: ", [task.id for task in best_schedule.alr.values()])
