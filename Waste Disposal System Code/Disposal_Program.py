import time
import random
import sys
sys.path.append('../')

from Common_Libraries.p3b_lib import *

import os
from Common_Libraries.repeating_timer_lib import repeating_timer

def update_sim():
    try:
        my_table.ping()
    except Exception as error_update_sim:
        print (error_update_sim)

### Constants
speed = 0.2 #Qbot's speed

### Initialize the QuanserSim Environment
my_table = servo_table()
arm = qarm()
arm.home()
bot = qbot(speed)

##---------------------------------------------------------------------------------------
## STUDENT CODE BEGINS
##---------------------------------------------------------------------------------------
#Initialize Variables
bin_id_on_bot = "Bin00"                 # the ID of the container on the bot
bin_id_on_table = "Bin00"               # the id of the container on the table
target_bin = ""                         # the name of the destination bin as a string
num_container = 0                       # the number of the containers on the robot
mass_on_bot = 0                         # the total mass of all containers on the bot
mass_on_table = 0                       #the total mass of the containers on the table
bot_speed = 0.2
GRAB_POSITION = [0.665, 0.0, 0.2504]    # the XYZ position of the container on table
DROP_POSITION = [[-0.1, -0.3865, 0.4826],
                 [-0.0284, -0.4054, 0.4826],
                 [0.0635, -0.4014, 0.4826]]  # the 3 possible XYZ positions to drop the containers



#takes a table given to it and determines its average
def calc_avg(table):
    total = 0
    for index in table:
        total += index
    return total/len(table)

#assesses whether the bottle on the table should be loaded on bot
def should_take_container():
    print((bin_id_on_bot != bin_id_on_table), (bin_id_on_bot != "Bin00"), (mass_on_table + mass_on_bot > 90), (num_container >= 3))
    print(bin_id_on_bot, bin_id_on_table)
    #if the any 3 conditions are met, the loading stops (return false)
    if (bin_id_on_bot != bin_id_on_table):
        print(1)
        conditions_met = False
        if(bin_id_on_bot == "Bin00"):
            print(1,2)
            conditions_met = True 
    elif(mass_on_table + mass_on_bot > 90):
        print(2)
        conditions_met = False
    elif(num_container >= 3):
        print(3)
        conditions_met = False

    #same container on table & bot, less than 90g, less than 2 containers
    else:
        print(4)
        conditions_met = True
    return conditions_met

#updates the mass on table
def set_mass_table(mass):
    mass_on_table = mass

#update the mass
def set_mass_bot(mass):
    mass_on_bot = mass

def set_num_container(num):
    num_container = num

#set the bin id 
def set_target_bin(bin_id):
    target_bin = bin_id
 
def set_bot_bin(bin_id):
    bin_id_on_bot = bin_id

def set_table_bin(bin_id):
    bin_id_on_table = bin_id




#grabs container from table and moves home
def grab_container():
    arm.move_arm(GRAB_POSITION[0],
                 GRAB_POSITION[1],
                 GRAB_POSITION[2])
    #make wrist perpendicular to container
    arm.control_gripper(55)
    arm.move_arm(0.4064, 0.0, 0.4826)

#moves container to appropriate position
def move_container():
    arm.move_arm(DROP_POSITION[num_container][0],
                 DROP_POSITION[num_container][1],
                 DROP_POSITION[num_container][2])
    arm.control_gripper(-30)
    arm.rotate_elbow(-50)
    arm.home()


##Orin's code that doesn't quite work yet




#Takes the QBot from the bin around the loop to home
def qbot_to_pickup():
    bot_speed = 0.5

    #move the robot to the two line junction
    bot.activate_ultrasonic_sensor()
    trip_time = time_of_trip(bot.read_ultrasonic_sensor("Bin04"), bot_speed)
    start = time.time()
    while(time.time()-start < trip_time):
        lost_lines, wheel_velocities = bot.follow_line(bot_speed)
        bot.forward_velocity(wheel_velocities)

        
    #move the robot past the juntion
    trip_time = time_of_trip(0.75, bot_speed)
    start = time.time()
    while(time.time()-start < trip_time):
        bot.forward_velocity([bot_speed, bot_speed])

    #get bot past the loop and back home    
    bot_speed = 0.1
    lost_lines, dist_from_line = bot.follow_line(bot_speed)
    while(lost_lines <= 0):
        lost_lines, dist_from_line = bot.follow_line(bot_speed)
        bot.forward_velocity(dist_from_line)

    #ease bot to original pick up position
    bot.forward_time(0.5)
    bot.stop()

#move Qbot to bin position and deposit container
def qbot_to_bin():
    bot_speed = 0.5
    bot.activate_ultrasonic_sensor()
    
    #turn bot
    bot.rotate(180)
    time.sleep(0.2)

    #move bot quickly to correct bin
    print(target_bin)
    trip_time = time_of_trip(bot.read_ultrasonic_sensor(target_bin) +.3, bot_speed)
    start = time.time()
    while(time.time()-start<trip_time):
        lost_lines, wheel_velocities = bot.follow_line(bot_speed)
        bot.forward_velocity(wheel_velocities)


    #move bot directly next to bin
    dist_readings = bot.read_ultrasonic_sensor(target_bin) #distance from bin
    dist_readings_check = dist_readings

    while (dist_readings > 0.06) and (dist_readings_check >= dist_readings):
        if(dist_readings != dist_readings_check):
            dist_readings_check = dist_readings
        dist_readings = bot.read_ultrasonic_sensor(target_bin) ##Puts the outputs of the colour sensor into a list
        lost_lines, wheel_velocities = bot.follow_line(bot_speed)
        bot.forward_velocity(wheel_velocities)

        
    #transfer contents
    bot.stop()
    print("stop")
    bot.activate_actuator()
    bot.dump()

#calculates the time of a trip based on distance and bot speed
def time_of_trip(distance, speed):
    return (distance/speed)
##################################################################################################################################
#main code execution
while(True):
    print(target_bin, bin_id_on_bot, bin_id_on_table)
    #if open table, new container
    if(mass_on_table == 0):
        material, mass, bin_id = my_table.container_properties(random.randrange(1,7))
        my_table.dispense_container()
        mass_on_table = (mass+mass_on_table)
        bin_id_on_table = bin_id

    #if bot can take table container
    if(should_take_container()):

        #reset variables to new container
        target_bin = bin_id
        bin_id_on_bot = bin_id
        bin_id_on_table = "Bin00"

        mass_on_bot = (mass_on_table + mass_on_bot)
        mass_on_table = 0
        num_container = num_container+1
        
        #loads container
        grab_container()
        move_container()

    #drop off contaianer(s) and return for more
    else:
        qbot_to_bin()
        qbot_to_pickup()
        
        #reset variables to new container
        target_bin = "Bin00"
        bin_id_on_bot = "Bin00"
        mass_on_bot = 0
        num_container = 0
        

##---------------------------------------------------------------------------------------
## STUDENT CODE ENDS
##---------------------------------------------------------------------------------------
update_thread = repeating_timer(2,update_sim)
