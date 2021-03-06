import os
import types
from python.Util import logger
from python import IScheduler
from python.Util import Conf
# TODO add init/fin call function mode
class IApplication:
    def __init__(self, rootdir, name, config_path=None):
        self.id = None
        self.flag = None
        self.cfg=None
        self.name = name
        self.app_boot=[]
        self.res_dir = ""   # the directory of result
        self.args = {}      # the args for app_boot
        self.data = {}      # k-v

        self.app_init_boot = []     # the prog for app init
        self.app_init_extra = {}    # the args/data for running init prog

        self.app_fin_boot = []
        self.app_fin_extra = {}
        self.scheduler = None
        self.specifiedWorker = None
        self.log = logger.getLogger(self.name,applog=True)
        self.status = {'scheduler':None,
                       'boot':None,
                       'resdir':None,
                       'data':None}
        if os.path.exists(os.path.abspath(rootdir)):
            self.rootdir = os.path.abspath(rootdir)
            self.status['resdir'] = True
        else:
            self.log.error('Can not find root dir=%s'%rootdir)
            

    def set_id(self,id):
        self.id = id

    def set_scheduler(self, scheduler):
        if not callable(scheduler) or not issubclass(scheduler,IScheduler.IScheduler):
            # TODO unrecognized scheduler
            self.log.error('Scheduler %s can not be recognized'%scheduler)
            return
        else:
            self.scheduler = scheduler
            self.status['scheduler'] = True
    '''
    def set_worker(self, worker):
        if not callable(worker) or not issubclass(worker, IAPPWorker):
            self.log.error('Costumed Worker %s can not be recognized, use default worker'%worker)
            return
        else:
            self.specifiedWorker = worker
            self.status['worker'] = True
    '''
    def get_scheduler(self):
        return self.scheduler

    def set_init_boot(self,init_boot):
        if type(init_boot) is types.ListType:
            self.app_init_boot.extend(init_boot)
        else:
            self.app_init_boot.append(init_boot)
    def set_init_extra(self, init_extra):
        """
        :param init_extra: dict
        :return:
        """
        if not type(init_extra) is types.DictionaryType:
            return
        self.app_init_extra=dict(self.app_init_extra,**init_extra)
    def set_fin_boot(self, fin_boot):
        if type(fin_boot) is types.ListType:
            self.app_fin_boot.extend(fin_boot)
        else:
            self.app_fin_boot.append(fin_boot)
    def set_fin_extra(self, fin_extra):
        """
        :param fin_extra: dict
        :return:
        """
        if not type(fin_extra) is types.DictionaryType:
            return
        self.app_fin_extra=dict(self.app_fin_extra,**fin_extra)
    def set_boot(self, boot_list):
        if type(boot_list) is types.ListType:
            self.app_boot.extend(boot_list)
        else:
            self.app_boot.append(boot_list)
        for boot in self.app_boot:
            if not os.path.exists(boot):
                if not os.path.exists(self.rootdir+'/'+boot):
                    self.log.error('Error: Can not find boot script %s'%boot)
                    return
                else:
                    self.app_boot.insert(self.app_boot.index(boot),self.rootdir+'/'+boot)
                    self.app_boot.remove(boot)
        self.status['boot'] = True

    def set_resdir(self, res_dir):
        self.res_dir = os.path.abspath(res_dir)
        if not os.path.exists(self.res_dir):
            os.mkdir(self.res_dir)
    def set_rootdir(self, rootdir):
        if os.path.exists(rootdir):
            self.rootdir = os.path.abspath(rootdir)

    def set_worker(self,worker_class):
        worker_module_path = None
        worker_file = worker_class
        if not worker_file.endswith('.py'):
            worker_file = worker_file + '.py'
        if os.path.exists(worker_file):
            worker_module_path = os.path.abspath(worker_file)
            self.log.debug('find specific worker module %s' % os.path.basename(worker_module_path))
        elif os.path.exists(os.environ['DistJETPATH'] + '/python/Application/' + worker_file):
            worker_module_path = os.path.abspath(os.environ['DistJETPATH'] + '/python/Application/' + worker_file)
            self.log.debug('find specific worker module %s' % os.path.basename(worker_module_path))
        else:
            fflag = False
            for dd in os.listdir(os.environ['DistJETPATH'] + '/Application'):
                prepath = os.environ['DistJETPATH'] + '/Application/' + dd
                if os.path.exists(prepath + '/' + worker_file):
                    fflag = True
                    worker_module_path = prepath + '/' + worker_file
            if not fflag:
                self.log.warning('Can not find specific worker module ,use default')
        self.specifiedWorker = worker_module_path

    def split(self):
        """
        this method needs to be overwrite by user to split data into key-value pattern
        :return: k-v data
        """
        raise NotImplementedError

    def merge(self, tasklist):
        """
        this method needs to be overwrite by user to merge the result data
        :param tasklist:{tid:taskobj}
        :return:
        """
        raise NotImplementedError

    def setup(self):
        """
        this method is called by APPManager, tell worker how to setup env
        :return: list of command, return [E] means error, return None means no need to setup
        """
        raise NotImplementedError

    def checkApp(self):
        for k,v in self.status.items():
            if self.status[k] is None:
                self.log.error('Error: App %s is not allow or lack'%k)
                return False
        return True

    def setStatus(self,item,val=True):
        self.status[item]=val