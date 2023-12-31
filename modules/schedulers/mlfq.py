from typing import List, Callable

from models import Process
from modules import Processor
from ..schedulers import Scheduler, FCFS, SJF, PriorityNP, RoundRobin

class MLFQ(Scheduler):
    name: str = "Multilevel Feedback Queue (MLFQ)"
    is_multilevel: bool = True

    def __init__(self, processes: List[Process], processor: Processor, time_quantums: List[int], last_layer: Callable[[List[Process], Processor], Scheduler]):
        super().__init__(processes, processor)
        self.__layers: List[Scheduler] = []

        for p in processes:
            # -1 signifies unqueued processes
            p.queue_level = -1

        # Initialize the layers
        for layer_num, time_quantum in enumerate(time_quantums):
            rr_instance = RoundRobin.factory(time_quantum, is_decrement_automatic=False)
            layer = rr_instance(processes if layer_num == 0 else [], processor)
            
            # Ensures that only the running round robin is ticking its time window
            # The l = layer is a workaround to keep the layer block scoped, as layer is local scoped 
            self._processor.on_clear(lambda _, l = layer : self._processor.off_tick(l.decrement_time_window))
            self.__layers.append(layer)
        
        self.__layers.append(last_layer(processes, processor)) 

    @staticmethod
    def last_layer_choices():
        return [FCFS, SJF, PriorityNP]
    
    @classmethod
    def factory(cls, time_quantums: List[int], last_layer: Callable[[List[Process], Processor], Scheduler]):
        """ A method that returns a partially instantiated scheduler that can be latched onto the operating system for use. """
        partialized_instance: Callable[[List[Process], Processor], cls] = lambda pl, p : cls(pl, p, time_quantums, last_layer)
        return partialized_instance

    @property
    def round_robin_layers(self) -> List[RoundRobin]:
        return self.__layers[:-1] # pyright: ignore[reportGeneralTypeIssues]
    
    @property
    def last_layer(self):
        return self.__layers[-1]

    def is_queued(self, process: Process):
        return any(process in layer._ready_queue for layer in self.__layers)

    def enqueue(self, *processes: Process):
        # Queue the arrived processes to their next queue levels
        for p in sorted(processes, key=lambda p : (p.arrival, p.pid)):
            p.queue_level += 1

            if p.queue_level < len(self.__layers):
                self.__layers[p.queue_level].enqueue(p)

    def run(self, timestamp: int, is_allowed_to_preempt: bool = True):
        if self._processor.is_idle:
            arrived_processes = self.get_arrived_processes(timestamp)
                
            if len(arrived_processes) > 0:
                self.enqueue(*arrived_processes)

            # Get the topmost round robin layer's ready queue
            for rr_layer in self.round_robin_layers:
                if len(rr_layer._ready_queue) > 0:
                    self._processor.on_tick(rr_layer.decrement_time_window)
                    self._ready_queue = rr_layer._ready_queue
                    break
            
            # If there are no more processes on the top layers work on the last layer
            if len(self._ready_queue) == 0:
                self._ready_queue = self.last_layer._ready_queue

        return self._ready_queue
