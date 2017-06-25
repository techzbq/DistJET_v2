import ValApp
from python.IScheduler import SimpleScheduler
def run(config_path=None):
    app = ValApp.ValApp('/afs/ihep.ac.cn/users/z/zhaobq/workerSpace/DistJET_v2/Application/Validation','ValApp',config_path)
    app.set_boot('analysis.py')
    app.set_resdir("/afs/ihep.ac.cn/users/z/zhaobq/workerSpace/DistJET_v2/test/valtest/resdir")
    app.set_scheduler(SimpleScheduler)
    return app

