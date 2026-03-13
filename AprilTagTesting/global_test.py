import Again as a
import time
import json

field = json.load(open("AprilTagTesting/Storm.json"))
'''print(field["tags"][0]["pose"]["translation"]["x"])
for tag in field["tags"]:
    print(tag["pose"]["translation"]["x"])'''

#0 degrees faces spinny wheels



'''
rot 0
    field x = -x
    field y = -z
rot 90
    field x = -z
    field y = x
rot 180
    field x = x
    field y = z
rot 270
    field x = z
    field y = -x

'''

'''
if [tag][rot] = 0:
    facing front(spinny wheels)
    local x = field x - camera x
    local y = field y - camera z
elif [tag][rot] = 90:
    facing right
    local x = field x - camera z
    local y = field y + camera x
elif [tag][rot] = 180:
    facing back (home)
    local x = field x + camera x
    local y = field y + camera z
elif [tag][rot] = 270:
    facing left
    local x = field x + camera z
    local y = field y - camera x

'''


'''while True:
    a.Estimate()
    if(len(a.tags_ID) != 0):
        print(field["tags"][a.tags_ID[0]]["pose"]["translation"]["x"])
        print(a.tags_ID[0])
        break'''


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
            #print("Field X: " + str(field["tags"][a.tags_ID[i]]["pose"]["translation"]["x"]) + " cm")
            #print("Field Y: " + str(field["tags"][a.tags_ID[i]]["pose"]["translation"]["y"]) + " cm")
            local_x = field["tags"][a.tags_ID[i]]["pose"]["translation"]["x"] - a.poses_x[i]
            local_y = field["tags"][a.tags_ID[i]]["pose"]["translation"]["y"] - a.poses_z[i]

        elif(tag_rot == 90):
            print("Facing right side")
            #print("Field X: " + str(field["tags"][a.tags_ID[i]]["pose"]["translation"]["x"]) + " cm")
            #print("Field Y: " + str(field["tags"][a.tags_ID[i]]["pose"]["translation"]["y"]) + " cm")
            local_x = field["tags"][a.tags_ID[i]]["pose"]["translation"]["x"] - a.poses_z[i]
            local_y = field["tags"][a.tags_ID[i]]["pose"]["translation"]["y"] + a.poses_x[i]
        elif(tag_rot == 180):
            print("Facing back (home)")
            #print("Field X: " + str(field["tags"][a.tags_ID[i]]["pose"]["translation"]["x"]) + " cm")
            #print("Field Y: " + str(field["tags"][a.tags_ID[i]]["pose"]["translation"]["y"]) + " cm")
            local_x = field["tags"][a.tags_ID[i]]["pose"]["translation"]["x"] + a.poses_x[i]
            local_y = field["tags"][a.tags_ID[i]]["pose"]["translation"]["y"] + a.poses_z[i]
        elif(tag_rot == 270):
            print("Facing left side")
            #print("Field X: " + str(field["tags"][a.tags_ID[i]]["pose"]["translation"]["x"]) + " cm")
            #print("Field Y: " + str(field["tags"][a.tags_ID[i]]["pose"]["translation"]["y"]) + " cm")
            local_x = field["tags"][a.tags_ID[i]]["pose"]["translation"]["x"] + a.poses_z[i]
            local_y = field["tags"][a.tags_ID[i]]["pose"]["translation"]["y"] - a.poses_x[i]
        print("Camera X: " + str(a.poses_x[i]) + " in")
        print("Camera Y: " + str(a.poses_y[i]) + " in")
        print("Local X: " + str(local_x) + " in")
        print("Local Y: " + str(local_y) + " in")
        print("Rotation: " + str(tag_rot + a.poses_rot_y[i]) + " degrees")
        #print("Y: " + str(a.poses_y[i]) + " cm")
        #print("Z: " + str(a.poses_z[i]) + " cm")
        #print(field["tags"][a.tags_ID[i]]["pose"]["translation"]["x"] + a.poses_x[i])
        '''print("Y: " + str(a.poses_y[i]) + " cm")
        print("Z: " + str(a.poses_z[i]) + " cm")
        print("Rotation X: " + str(a.poses_rot_x[i]))
        print("Rotation Y: " + str(a.poses_rot_y[i])) #Most important one (left/right)
        print("Rotation Z: " + str(a.poses_rot_z[i]))'''

        print()
        break
    time.sleep(0.5)
