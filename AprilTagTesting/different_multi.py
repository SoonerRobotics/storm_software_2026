import almost_real as a
import time
import json

field = json.load(open("AprilTagTesting/Storm.json"))

'''local_x = 0
local_y = 0
rotation = 0'''
while True:
    a.Estimate()

    local_x = 0
    local_y = 0
    rotation = 700

    tag_to_use = 0

    curr_local_x = 0
    curr_local_y = 0
    curr_rotation = 0

    for i in range(len(a.tags_ID)):
        if a.poses_rot_y[i] < rotation:
            tag_to_use = i

    tag_rot = field["tags"][a.tags_ID[tag_to_use]]["pose"]["rotation"]
    if(tag_rot == 0):
        print("Facing front(spinny wheels)")
        curr_local_x += field["tags"][a.tags_ID[tag_to_use]]["pose"]["translation"]["x"] - a.poses_x[tag_to_use]
        curr_local_y += field["tags"][a.tags_ID[tag_to_use]]["pose"]["translation"]["y"] - a.poses_z[tag_to_use]

    elif(tag_rot == 90):
        print("Facing right side")
        curr_local_x += field["tags"][a.tags_ID[tag_to_use]]["pose"]["translation"]["x"] - a.poses_z[tag_to_use]
        curr_local_y += field["tags"][a.tags_ID[tag_to_use]]["pose"]["translation"]["y"] + a.poses_x[tag_to_use]

    elif(tag_rot == 180):
        print("Facing back (home)")
        curr_local_x += field["tags"][a.tags_ID[tag_to_use]]["pose"]["translation"]["x"] + a.poses_x[tag_to_use]
        curr_local_y += field["tags"][a.tags_ID[tag_to_use]]["pose"]["translation"]["y"] + a.poses_z[tag_to_use]

    elif(tag_rot == 270):
        print("Facing left side")
        curr_local_x += field["tags"][a.tags_ID[tag_to_use]]["pose"]["translation"]["x"] + a.poses_z[tag_to_use]
        curr_local_y += field["tags"][a.tags_ID[tag_to_use]]["pose"]["translation"]["y"] - a.poses_x[tag_to_use]

    curr_rotation = tag_rot + a.poses_rot_y[tag_to_use]
        
    curr_rotation = abs(curr_rotation)
    print("Camera X (horizontal): " + str(a.poses_x[tag_to_use]) + " in")
    print("Camera Z (depth): " + str(a.poses_z[tag_to_use]) + " in")
    print("Individual Field X: " + str(curr_local_x) + " in")
    print("Individual Field Y: " + str(curr_local_y) + " in")
    print("ID: " + str(a.tags_ID[tag_to_use]))
    print("Rotation: " + str(curr_rotation) + " degrees")

    print()
    time.sleep(0.25)