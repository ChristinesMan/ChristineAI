from mpu6050 import mpu6050
import math
import time

AccelXRecord = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
AccelYRecord = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
GyroXRecord = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
GyroYRecord = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
GyroZRecord = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
SampleSize = 20
LoopIndex = 0
sensor = mpu6050(0x68)

while True:
    data = sensor.get_all_data()
    LoopCycle = LoopIndex % SampleSize
    AccelXRecord[LoopCycle] = data[0]['x']
    AccelYRecord[LoopCycle] = data[0]['y']
    GyroXRecord[LoopCycle] = abs(data[1]['x'])
    GyroYRecord[LoopCycle] = abs(data[1]['y'])
    GyroZRecord[LoopCycle] = abs(data[1]['z'])
    if ( LoopCycle == 0 ):
        print("AccelX: {0:.3f}  AccelY: {1:.3f}  GyroX: {2:.3f}  GyroY: {3:.3f}  GyroZ: {4:.3f}".format(sum(AccelXRecord) / SampleSize, sum(AccelYRecord) / SampleSize, sum(GyroXRecord) / SampleSize, sum(GyroYRecord) / SampleSize, sum(GyroZRecord) / SampleSize))
    # GyroAverage = ((GyroAverage * GyroAverageWindow) + Gyro) / (GyroAverageWindow + 1)
    LoopIndex += 1

# # Power management registers
# power_mgmt_1 = 0x6b
# power_mgmt_2 = 0x6c

# gyro_scale = 131.0
# accel_scale = 16384.0

# address = 0x68  # This is the address value read via the i2cdetect command

# def read_all():
#     raw_gyro_data = bus.read_i2c_block_data(address, 0x43, 6)
#     raw_accel_data = bus.read_i2c_block_data(address, 0x3b, 6)

#     gyro_scaled_x = twos_compliment((raw_gyro_data[0] << 8) + raw_gyro_data[1]) / gyro_scale
#     gyro_scaled_y = twos_compliment((raw_gyro_data[2] << 8) + raw_gyro_data[3]) / gyro_scale
#     gyro_scaled_z = twos_compliment((raw_gyro_data[4] << 8) + raw_gyro_data[5]) / gyro_scale

#     accel_scaled_x = twos_compliment((raw_accel_data[0] << 8) + raw_accel_data[1]) / accel_scale
#     accel_scaled_y = twos_compliment((raw_accel_data[2] << 8) + raw_accel_data[3]) / accel_scale
#     accel_scaled_z = twos_compliment((raw_accel_data[4] << 8) + raw_accel_data[5]) / accel_scale

#     return (gyro_scaled_x, gyro_scaled_y, gyro_scaled_z, accel_scaled_x, accel_scaled_y, accel_scaled_z)

# def twos_compliment(val):
#     if (val >= 0x8000):
#         return -((65535 - val) + 1)
#     else:
#         return val

# def dist(a, b):
#     return math.sqrt((a * a) + (b * b))

# def get_y_rotation(x,y,z):
#     radians = math.atan2(x, dist(y,z))
#     return -math.degrees(radians)

# def get_x_rotation(x,y,z):
#     radians = math.atan2(y, dist(x,z))
#     return math.degrees(radians)

# bus = smbus.SMBus(0)  # or bus = smbus.SMBus(1) for Revision 2 boards

# # Now wake the 6050 up as it starts in sleep mode
# bus.write_byte_data(address, power_mgmt_1, 0)

# now = time.time()

# K = 0.98
# K1 = 1 - K

# time_diff = 0.01

# (gyro_scaled_x, gyro_scaled_y, gyro_scaled_z, accel_scaled_x, accel_scaled_y, accel_scaled_z) = read_all()

# last_x = get_x_rotation(accel_scaled_x, accel_scaled_y, accel_scaled_z)
# last_y = get_y_rotation(accel_scaled_x, accel_scaled_y, accel_scaled_z)

# gyro_offset_x = gyro_scaled_x
# gyro_offset_y = gyro_scaled_y

# gyro_total_x = (last_x) - gyro_offset_x
# gyro_total_y = (last_y) - gyro_offset_y

# print("{0:.4f} {1:.2f} {2:.2f} {3:.2f} {4:.2f} {5:.2f} {6:.2f}".format( time.time() - now, (last_x), gyro_total_x, (last_x), (last_y), gyro_total_y, (last_y)))

# for i in range(0, int(3.0 / time_diff)):
#     time.sleep(time_diff - 0.005)
    
#     (gyro_scaled_x, gyro_scaled_y, gyro_scaled_z, accel_scaled_x, accel_scaled_y, accel_scaled_z) = read_all()
    
#     gyro_scaled_x -= gyro_offset_x
#     gyro_scaled_y -= gyro_offset_y
    
#     gyro_x_delta = (gyro_scaled_x * time_diff)
#     gyro_y_delta = (gyro_scaled_y * time_diff)

#     gyro_total_x += gyro_x_delta
#     gyro_total_y += gyro_y_delta

#     rotation_x = get_x_rotation(accel_scaled_x, accel_scaled_y, accel_scaled_z)
#     rotation_y = get_y_rotation(accel_scaled_x, accel_scaled_y, accel_scaled_z)

#     last_x = K * (last_x + gyro_x_delta) + (K1 * rotation_x)
#     last_y = K * (last_y + gyro_y_delta) + (K1 * rotation_y)
    
#     print("{0:.4f} {1:.2f} {2:.2f} {3:.2f} {4:.2f} {5:.2f} {6:.2f}".format( time.time() - now, (rotation_x), (gyro_total_x), (last_x), (rotation_y), (gyro_total_y), (last_y)))



# from mpu6050 import mpu6050
# sensor = mpu6050(0x68)
# accelerometer_data = sensor.get_accel_data()

# I can use this after cleaning it up. This may be good for converting the raw stuff to useable numbers, then I can figure out
# how to calculate the deviation and calibrate it, etc. 



# import smbus
# import math
# import time
# from MPU6050 import MPU6050
# from PID import PID
# import motor as MOTOR

# gyro_scale = 131.0
# accel_scale = 16384.0
# RAD_TO_DEG = 57.29578
# M_PI = 3.14159265358979323846

# address = 0x68  # This is the address value read via the i2cdetect command
# bus = smbus.SMBus(1)  # or bus = smbus.SMBus(1) for Revision 2 boards

# now = time.time()

# K = 0.98
# K1 = 1 - K

# time_diff = 0.01

# sensor = MPU6050(bus, address, "MPU6050")
# sensor.read_raw_data()  # Reads current data from the sensor

# rate_gyroX = 0.0
# rate_gyroY = 0.0
# rate_gyroZ = 0.0

# gyroAngleX = 0.0 
# gyroAngleY = 0.0 
# gyroAngleZ = 0.0 

# raw_accX = 0.0
# raw_accY = 0.0
# raw_accZ = 0.0

# rate_accX = 0.0
# rate_accY = 0.0
# rate_accZ = 0.0

# accAngX = 0.0

# CFangleX = 0.0
# CFangleX1 = 0.0

# K = 0.98

# FIX = -12.89

# #print "{0:.4f} {1:.2f} {2:.2f} {3:.2f} {4:.2f} {5:.2f} {6:.2f}".format( time.time() - now, (last_x), gyro_total_x, (last_x), (last_y), gyro_total_y, (last_y))

# def dist(a, b):
#     return math.sqrt((a * a) + (b * b))

# def get_y_rotation(x,y,z):
#     radians = math.atan2(x, dist(y,z))
#     return -math.degrees(radians)

# def get_x_rotation(x,y,z):
#     radians = math.atan2(y, dist(x,z))
#     return math.degrees(radians)

# p=PID(1.0,-0.04,0.0)
# p.setPoint(0.0)

# for i in range(0, int(300.0 / time_diff)):
#     time.sleep(time_diff - 0.005) 
    
#     sensor.read_raw_data()
    
#     # Gyroscope value Degree Per Second / Scalled Data
#     rate_gyroX = sensor.read_scaled_gyro_x()
#     rate_gyroY = sensor.read_scaled_gyro_y()
#     rate_gyroZ = sensor.read_scaled_gyro_z()
    
#     # The angle of the Gyroscope
#     gyroAngleX += rate_gyroX * time_diff 
#     gyroAngleY += rate_gyroY * time_diff 
#     gyroAngleZ += rate_gyroZ * time_diff 

#     # Accelerometer Raw Value
#     raw_accX = sensor.read_raw_accel_x()
#     raw_accY = sensor.read_raw_accel_y()
#     raw_accZ = sensor.read_raw_accel_z()
    
#     # Accelerometer value Degree Per Second / Scalled Data
#     rate_accX = sensor.read_scaled_accel_x()
#     rate_accY = sensor.read_scaled_accel_y()
#     rate_accZ = sensor.read_scaled_accel_z()
    
#     # http://ozzmaker.com/2013/04/18/success-with-a-balancing-robot-using-a-raspberry-pi/
#     accAngX = ( math.atan2(rate_accX, rate_accY) + M_PI ) * RAD_TO_DEG
#     CFangleX = K * ( CFangleX + rate_gyroX * time_diff) + (1 - K) * accAngX
    
#     # http://blog.bitify.co.uk/2013/11/reading-data-from-mpu-6050-on-raspberry.html 
#     accAngX1 = get_x_rotation(rate_accX, rate_accY, rate_accX)
#     CFangleX1 = ( K * ( CFangleX1 + rate_gyroX * time_diff) + (1 - K) * accAngX1 )
    
#     # Followed the Second example because it gives resonable pid reading
#     pid = p.update(CFangleX1)
    
#     if(pid > 0):
#         MOTOR.forward(pid)
#     else:
#         MOTOR.backward( (pid*-1) )
    
#     print "{0:.2f} {1:.2f} {2:.2f} {3:.2f} | {4:.2f} {5:.2f} | {6:.2f}".format( gyroAngleX, gyroAngleY , accAngX, CFangleX, accAngX1, CFangleX1, pid)





# This might be the best: http://blog.bitify.co.uk/2013/11/reading-data-from-mpu-6050-on-raspberry.html