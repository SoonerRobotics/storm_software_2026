import Again as a
import time


while True:
    a.Estimate()
    for i in range(len(a.tags_ID)):
        print("ID: " + str(a.tags_ID[i]))
        print("X: " + str(a.poses_x[i]) + " cm")
        print("Y: " + str(a.poses_y[i]) + " cm")
        print("Z: " + str(a.poses_z[i]) + " cm")
        print("Rotation X: " + str(a.poses_rot_x[i]))
        print("Rotation Y: " + str(a.poses_rot_y[i])) #Most important one (left/right)
        print("Rotation Z: " + str(a.poses_rot_z[i]))

        print()
    time.sleep(0.5)