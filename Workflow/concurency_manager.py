# concurrency_manager.py
from concurrent.futures import ThreadPoolExecutor
import queue
import threading

class ConcurrencyManager:
    def __init__(self, max_workers=4):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.task_queue = queue.Queue()
        self.results_queue = queue.Queue()
        self.active = False
        
    def start_processing(self, tasks):
        self.active = True
        futures = []
        for task in tasks:
            future = self.executor.submit(task)
            futures.append(future)
        return futures
        
    def monitor_tasks(self, futures, callback):
        """Monitor task progress and report results"""
        def _monitor():
            completed = 0
            total = len(futures)
            for future in futures:
                try:
                    result = future.result()
                    completed += 1
                    progress = (completed / total) * 100
                    callback(progress, result)
                except Exception as e:
                    callback(-1, str(e))
        
        thread = threading.Thread(target=_monitor)
        thread.daemon = True
        thread.start()