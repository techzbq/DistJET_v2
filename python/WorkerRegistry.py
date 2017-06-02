wRegistery_log = None

import threading
import time
import traceback

from python.Util.Conf import Config


class WorkerStatus:
    NEW = -1
    INITILAZED = 0
    IDLE = 1
    RUNNING = 2
    ERROR = 3
    LOST = 4
    FINALIZED = 5

class WorkerEntry:
    """
    contain worker information and task queue
    """
    def __init__(self, wid, w_uuid, max_capacity):
        self.wid = wid
        self.policy = Config()
        self.w_uuid = w_uuid
        self.registration_time =time.time()
        self.last_contact_time = self.registration_time
        self.idle_time = 0

        self.max_capacity = max_capacity
        self.assigned = 0

        self.status = WorkerStatus.NEW
        self.alive_lock = threading.RLock()
        self.alive = True

    def capacity(self):
        return self.max_capacity-self.assigned

    def isLost(self):
        if self.policy.getPolicyattr('LOST_WORKER_TIMEOUT'):
            return time.time()-self.last_contact_time > self.policy.getPolicyattr('LOST_WORKER_TIMEOUT')
        return False

    def getStatus(self):
        return self.status
    def isIdle_timeout(self):
        return self.idle_time and self.policy.getPolicyattr('IDLE_WORKER_TIMEOUT') and time.time()-self.idle_time > self.policy.getPolicyattr('IDLE_WORKER_TIMEOUT')

class WorkerRegistry:
    def __init__(self):
        self.__all_workers={}           # wid: worker_entry
        self.__all_workers_uuid = {}    # w_uuid: wid
        self.last_wid = 0
        self.lock = threading.RLock()

        #self.__alive_workers = []       # w_uuid

    def size(self):
        return len(self.__all_workers)

    def add_worker(self, w_uuid, max_capacity):
        wRegistery_log.debug('[WorkerRegistry] Before add worker')
        self.lock.acquire()
        try:
            if self.__all_workers_uuid.has_key(w_uuid):
                wid = self.__all_workers_uuid[w_uuid]
                wRegistery_log.warning('worker already registered: wid=%d, worker_uuid=%s',wid,w_uuid)
                return None
            else:
                self.last_wid+=1
                w = WorkerEntry(self.last_wid, w_uuid, max_capacity)
                self.__all_workers[self.last_wid] = w
                self.__all_workers_uuid[w_uuid] = self.last_wid
                wRegistery_log.info('new worker registered: wid=%d, worker_uuid=%s',self.last_wid, w_uuid)
                return w
        except:
            wRegistery_log.error('[WorkerRegistry]: Error occurs when adding worker, msg=%s', traceback.format_exc())
        finally:
            self.lock.release()
            wRegistery_log.debug('[WorkerRegistry] After add worker')

    def remove_worker(self, wid):
        self.lock.acquire()
        try:
            w_uuid = self.__all_workers[wid].w_uuid
        except KeyError:
            wRegistery_log.warning('attempt to remove not registered worker: wid=%d', wid)
            return False
        else:
            if not self.__all_workers[wid].alive:
                wRegistery_log.error('attempt to remove alive worker: wid=%d',wid)
                return False
            wRegistery_log.info('worker removed: wid=%d',wid)
            try:
                del(self.__all_workers[wid])
                del(self.__all_workers_uuid[w_uuid])
            except KeyError:
                wRegistery_log.warning('[WorkerRegistry]: can not find worker when remove worker=%d, uuid=%s', wid, w_uuid)
                return False
        finally:
            self.lock.release()
        return True

    def get_entry(self,wid):
        return self.__all_workers[wid]

    def get_by_uuid(self, w_uuid):
        return self.get_entry(self.__all_workers_uuid[w_uuid])

    def get_worker_list(self):
        return self.__all_workers.values()

    def __iter__(self):
        return self.__all_workers.copy().__iter__()
