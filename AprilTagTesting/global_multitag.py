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
    rotation = 0

    for i in range(len(a.tags_ID)):
        curr_local_x = 0
        curr_local_y = 0
        curr_rotation = 0

        tag_rot = field["tags"][a.tags_ID[i]]["pose"]["rotation"]
        if(tag_rot == 0):
            print("Facing front(spinny wheels)")
            curr_local_x += field["tags"][a.tags_ID[i]]["pose"]["translation"]["x"] - a.poses_x[i]
            curr_local_y += field["tags"][a.tags_ID[i]]["pose"]["translation"]["y"] - a.poses_z[i]

        elif(tag_rot == 90):
            print("Facing right side")
            curr_local_x += field["tags"][a.tags_ID[i]]["pose"]["translation"]["x"] - a.poses_z[i]
            curr_local_y += field["tags"][a.tags_ID[i]]["pose"]["translation"]["y"] + a.poses_x[i]

        elif(tag_rot == 180):
            print("Facing back (home)")
            curr_local_x += field["tags"][a.tags_ID[i]]["pose"]["translation"]["x"] + a.poses_x[i]
            curr_local_y += field["tags"][a.tags_ID[i]]["pose"]["translation"]["y"] + a.poses_z[i]

        elif(tag_rot == 270):
            print("Facing left side")
            curr_local_x += field["tags"][a.tags_ID[i]]["pose"]["translation"]["x"] + a.poses_z[i]
            curr_local_y += field["tags"][a.tags_ID[i]]["pose"]["translation"]["y"] - a.poses_x[i]

        curr_rotation = tag_rot + a.poses_rot_y[i]

        local_x += curr_local_x
        local_y += curr_local_y
        
        rotation += abs(curr_rotation)
        print("Camera X (horizontal): " + str(a.poses_x[i]) + " in")
        print("Camera Z (depth): " + str(a.poses_z[i]) + " in")
        print("Individual Field X: " + str(curr_local_x) + " in")
        print("Individual Field Y: " + str(curr_local_y) + " in")
        print("ID: " + str(a.tags_ID[i]))
        print("Rotation: " + str(curr_rotation) + " degrees")

        print()
    if(len(a.tags_ID) != 0):
        print("Average Field X: " + str(local_x / len(a.tags_ID)) + " in")
        print("Average Field Y: " + str(local_y / len(a.tags_ID)) + " in")
        print("Average Rotation: " + str(curr_rotation / len(a.tags_ID)) + " degrees")
    time.sleep(0.25)
