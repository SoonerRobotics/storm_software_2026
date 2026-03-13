import almost_real as a
import time
import json

field = json.load(open("AprilTagTesting/Storm.json"))

local_x = 0
local_y = 0

while True:
    a.Estimate()
    for i in range(len(a.tags_ID)):
        print("ID: " + str(a.tags_ID[i]))
        print("X: " + str(a.poses_x[i]) + " cm")
        tag_rot = field["tags"][a.tags_ID[i]]["pose"]["rotation"]
        if(tag_rot == 0):
            print("Facing front(spinny wheels)")
            local_x = field["tags"][a.tags_ID[i]]["pose"]["translation"]["x"] - a.poses_x[i]
            local_y = field["tags"][a.tags_ID[i]]["pose"]["translation"]["y"] - a.poses_z[i]

        elif(tag_rot == 90):
            print("Facing right side")
            local_x = field["tags"][a.tags_ID[i]]["pose"]["translation"]["x"] - a.poses_z[i]
            local_y = field["tags"][a.tags_ID[i]]["pose"]["translation"]["y"] + a.poses_x[i]

        elif(tag_rot == 180):
            print("Facing back (home)")
            local_x = field["tags"][a.tags_ID[i]]["pose"]["translation"]["x"] + a.poses_x[i]
            local_y = field["tags"][a.tags_ID[i]]["pose"]["translation"]["y"] + a.poses_z[i]

        elif(tag_rot == 270):
            print("Facing left side")
            local_x = field["tags"][a.tags_ID[i]]["pose"]["translation"]["x"] + a.poses_z[i]
            local_y = field["tags"][a.tags_ID[i]]["pose"]["translation"]["y"] - a.poses_x[i]

        print("Camera X (horizontal): " + str(a.poses_x[i]) + " in")
        print("Camera Z (depth): " + str(a.poses_z[i]) + " in")
        print("Field X: " + str(local_x) + " in")
        print("Field Y: " + str(local_y) + " in")
        print("Rotation: " + str(tag_rot + a.poses_rot_y[i]) + " degrees")

        print()
        break
    time.sleep(0.25)
