import numpy as np
import yaml

## sacred staff
import os
import dotenv; dotenv.load_dotenv()
from sacred import Experiment
from sacred.observers import MongoObserver, FileStorageObserver
import pymongo
ex = Experiment('sensor_test')
if "username" in os.environ and "host" in os.environ and "password" in os.environ:
    client = pymongo.MongoClient(
        username=os.environ['username'],
        password=os.environ['password'],
        host=os.environ['host'],
        port=27018,
        authSource=os.environ['database'],
        tls=True,
        tlsCAFile=
        "/usr/local/share/ca-certificates/Yandex/YandexInternalRootCA.crt",
    )
    ex.observers.append(
        MongoObserver(client=client, db_name=os.environ['database']))
else:
    ex.observers.append(FileStorageObserver('logdir'))
    input("WARNING! No password for db. Confirm logging locally")
ex.add_config('params.yaml')

# import glob
# for source_file in glob.glob("**/*.py", recursive=True):
#     ex.add_source_file(source_file)
    
# @ex.capture
# def log(_run):
    # _run.log_scalar('', 12)

with open('params.yaml') as conf_file:
    config = yaml.safe_load(conf_file)
    
## Robot init
import rtde_control
import rtde_receive
rtde_c = rtde_control.RTDEControlInterface(config['ip'])
rtde_r = rtde_receive.RTDEReceiveInterface(config['ip'])

@ex.automain
def touch_sensor(_run):

    c_state = rtde_r.getActualTCPPose()
    if c_state[2] < config['safe_hight']:
        rtde_c.moveL(c_state[:2] + [config['safe_hight']] + c_state[3:6], *config['speed'])
    
    net_step=config['grid']['steps']
    p0 = config['left_upper_corner']
    p1 = config['right_down_corner']
    net_step[0] *= np.sign(p1[0]-p0[0])
    net_step[1] *= np.sign(p1[1]-p0[1])
    shape = [int((p1[0]-p0[0])//net_step[0]+1), int((p1[1]-p0[1])//net_step[1]+1)]
    print("Shape is", shape)
    net_save_hight = config['safe_hight']

    # shape = [10, 10]
    
    # shape = [10, 10]
    net_corner = p0
    net_massive = [
        [ [net_corner[0]+i*net_step[0], net_corner[1]+j*net_step[1]]
        for i in range(shape[0])]
        for j in range(shape[1])
    ]
    for i in range(1, len(net_massive), 2):
        net_massive[i] = net_massive[i][::-1]
        
    for point_line in net_massive:
        for point in point_line:
            print(point)
            point_results = {"target_coordinate": point,
                             "base_coordinate":[],
                             "force_z":[],
                             "vector_force":[],
                             "deformation":[],
                             "base_coordinate":[],
                             }
            c_state = rtde_r.getActualTCPPose()
            rtde_c.moveL(c_state[:2] + [net_save_hight] + c_state[3:6], *config['speed'])
            c_state = rtde_r.getActualTCPPose()
            rtde_c.moveL(point + c_state[2:6], *config['speed'])
            
            task_frame = [0, 0, 0, 0, 0, 0]
            selection_vector = [0, 0, 1, 0, 0, 0]
            wrench = [0, 0, -config['force'], 0, 0, 0]   # forced in Newtons
            force_type = 2
            limits = [2, 2, 1.5, 1, 1, 1]   # limits speeds in directions of main movement and deviations in others
            dt = 1.0/500  # 2ms

            # Execute 500Hz control loop for 4 seconds, each cycle is 2ms
            for i in range(200):
                rtde_c.initPeriod()
                # First move the robot down for 2 seconds, then up for 2 seconds
                rtde_c.forceMode(task_frame, selection_vector, wrench, force_type, limits)
                
                ## logging
                _run.log_scalar('base_coordinate', rtde_r.getActualTCPPose())
                point_results['base_coordinate'].append(rtde_r.getActualTCPPose())
                _run.log_scalar('force_z', rtde_r.getActualTCPForce()[2])
                point_results['force_z'].append(rtde_r.getActualTCPForce()[2])
                _run.log_scalar('vector_force', rtde_r.getActualTCPForce())
                point_results['vector_force'].append(rtde_r.getActualTCPForce())
                depth = max(0, config['sensor_hight']-rtde_r.getActualTCPPose()[2])
                _run.log_scalar('deformation', depth)
                point_results['deformation'].append(depth)
                #todo add sensor mesurement logging
                if depth > config['max_sensor_depth']:
                    break
                rtde_c.waitPeriod(dt)

            rtde_c.forceModeStop()
            _run.log_scalar('point_results', point_results)
            
    # for  j in range(10):
    _run.log_scalar('test_metrics', [4, 5])
    _run.log_scalar('test_metrics', [8, 9])
    _run.log_scalar('test_metrics', [12, 15])
            