from socket import *
import select
import threading
import random
import time


class Router():

    def __init__(self, router_id, inputs, outputs, timer=30):
        self.timer = timer
        self.timeout = 180
        self.garbage_timer = 120

        self.router_id = router_id
        self.input_port = inputs
        self.routing_table = {}    #{dest_id: [metric, next_hop, timeout_timer_second, garbage_timer_second]}
        self.routing_table[router_id] = [0, None, None, None] #initialization
        
        
        self.outputs_port = {}      #{dest_id: [metric, output_port]}
        for output in outputs:
            output_port, metric, dest_id = output.split('-')
            output_port, metric, dest_id = int(output_port), int(metric), int(dest_id)
            self.outputs_port[dest_id] = [metric, output_port]



    def timer_start(self):  
        """ timer function """
        self.send_packet()      # send packet before timer start(when a router turn on)
        timer_interval = random.uniform(self.timer * 0.8, self.timer * 1.2)
        timer = threading.Timer(timer_interval, self.timer_start)
        timer.start()
        
        
 
    def send_packet(self):
        """ send packet to neighbor router """
        s = socket(AF_INET, SOCK_DGRAM)
        for dest_id, values in self.outputs_port.items():
            output_port = values[1]
            packet = self.create_rip_packet(dest_id)
            s.sendto(packet, ("127.0.0.1", output_port))
            




    def check_timer_expire(self):
        """check timeout timer and garbage timer is expire or not"""
        del_router = []
        current_time = time.time()       

        for dest_id, values in self.routing_table.items():
            timeout_timer = self.routing_table[dest_id][2]
            garbage_timer = self.routing_table[dest_id][3]

            # check if timeout timer has expired
            if timeout_timer is not None:
                if ((current_time - timeout_timer) >= self.timeout):
                    metric = 16
                    close_timeout_timer = None
                    start_garbage_timer = time.time()
                    
                    self.routing_table[dest_id][0] = metric
                    self.routing_table[dest_id][2] = close_timeout_timer
                    self.routing_table[dest_id][3] = start_garbage_timer
                    
                    print("Router id:{} timerout".format(dest_id))
                    self.print_routing_table()

                    
            # check if garbage timer has expired
            elif garbage_timer is not None:
                if ((current_time - garbage_timer) >= self.garbage_timer):
                    close_garbage_timer = None
                    self.routing_table[dest_id][3] = close_garbage_timer
                    del_router.append(dest_id)


        if del_router != []:
            self.del_router(del_router)




    def del_router(self, router):
        """garbage timer has expired delete router"""
        for i in router:
            print("garbage-collection Router id:{}".format(i))
            del self.routing_table[i] 
        self.print_routing_table()



    def need_poison_reverse(self,next_hop, dest_sent_to):
        """ split horizon with poisoned reverse """
        if dest_sent_to in self.outputs_port: # neighbor
            if next_hop == dest_sent_to:
                return True

        return False


    
    def create_rip_packet(self, dest_sended_to):
        """ response packet of rip packet"""
        command = [2]   # command = 1 is request, 2 is response
        verison = [2]
        sender_router_id = [(self.router_id >> 8), self.router_id & 0xFF] 

        header = command + verison + sender_router_id
        header = bytearray(header)


        # create entry
        entries = bytearray()
        for dest_id, values in self.routing_table.items():
    
            # Address family identifier AF_INET(2)
            AF_INET = 2
            AFI = [(AF_INET >> 8), AF_INET & 0xFF]

            # Zero field(2 bytes)
            zero_field_1 = [0, 0]

            # Destination Route_ID
            dest_route_id = [
                                ((dest_id & 0xFF000000) >> 24),
                                ((dest_id & 0xFF0000) >> 16),
                                ((dest_id & 0xFF00) >> 8),
                                 (dest_id & 0xFF)
                             ]

            # Zero field(4 bytes)
            zero_field_2 = [0, 0, 0, 0]

            # Zero field(4 bytes)
            zero_field_3 = [0, 0, 0, 0]

    
            # Metric
            cost = values[0]
            next_hop = values[1]
            if self.need_poison_reverse(next_hop, dest_sended_to):
                cost = 16
            
            metric = [
                        ((cost & 0xFF000000) >> 24),
                        ((cost & 0xFF0000) >> 16),
                        ((cost & 0xFF00) >> 8),
                        (cost & 0xFF)
                      ]

            
            entry = AFI + zero_field_1 + dest_route_id + zero_field_2 + zero_field_3 + metric
            entry = bytearray(entry)
            entries += entry


        packet = header + entries
        return packet



    def check_recieve_packet(self, packet):
        """ checks the response packet """
        command = packet[0]
        version = packet[1]
        sender_router_id = (packet[2] << 8) | packet[3]
        
        if command != 2:
            print("command does not equal 2")
            return False

        if version != 2:
            print("version does not equal 2")
            return False
        
        if sender_router_id < 1 or sender_router_id > 64000:
            print("sender router id must be between 1 and 64000")
            return False

        if len(packet) < 24:
            print("packet must be at least 24 bytes long")
            return False
            
        return True



    def unpack_recieve_packet(self, packet):
        """read recieve packet"""
        
        if self.check_recieve_packet(packet):
            
            command = packet[0]
            version = packet[1]
            sender_router_id = (packet[2] << 8) | packet[3]

            entry_length = len(packet) - 4       #header length is 4 bytes
            num_entries = int(entry_length / 20)
            
            for i in range(num_entries):
                
                index = 4 + (i * 20)
                
                address_family_identifier = (packet[index] << 8) | packet[index + 1]          
                zero_field_2 = 0
                destination_route_id = (packet[index + 4] << 24) | (packet[index + 5] << 16) | (packet[index + 6] << 8) | packet[index + 7]
                zero_field_3 = 0
                zero_field_4 = 0
                metric = (packet[index + 16] << 24) | (packet[index + 17] << 16) | (packet[index + 18] << 8) | packet[index + 19]            


                self.update_routing_table(destination_route_id, sender_router_id, metric)

        

    def update_routing_table(self, dest_router_id, sender_router_id, new_metric):
        """ process recieve data to update the routing table """
        trig_updates = False 
                
        if dest_router_id != self.router_id:
            # Add New Router
            if dest_router_id not in self.routing_table:
                total_metric = min(self.outputs_port[sender_router_id][0] + new_metric, 16)
                next_hop = sender_router_id

                if total_metric < 16:
                    start_timeout = time.time()
                    self.routing_table[dest_router_id] = [total_metric, next_hop, start_timeout, None]


            # Router already in the table, update table
            elif dest_router_id in self.routing_table:
                current_metric = self.routing_table[dest_router_id][0]
                total_metric = min(self.outputs_port[sender_router_id][0] + new_metric, 16)
                next_hop = self.routing_table[dest_router_id][1]

                
                if sender_router_id == next_hop:
                    if total_metric < 16:
                        start_timeout = time.time()
                        self.routing_table[dest_router_id] = [total_metric, next_hop, start_timeout, None]                        


                            
                    elif total_metric == 16:
                        if current_metric == total_metric == 16: # keep the timer running
                            pass
                        
                        elif current_metric != total_metric and current_metric != 16:
                            start_garbage_timer = time.time()
                            self.routing_table[dest_router_id] = [16, next_hop, None, start_garbage_timer]
                            trig_updates = True  #Router become invaild, trigered update

                            
                elif total_metric < 16:
                    if total_metric < current_metric:
                        next_hop = sender_router_id
                        start_timeout = time.time()
                        self.routing_table[dest_router_id] = [total_metric, next_hop, start_timeout, None]


        if trig_updates:
            self.send_packet()

        

            

        
            
    def print_routing_table(self):
        """print the routing table"""
        current_time = time.time()

        print("=======================================================================================")
        print("|  Router ID: {}                                                                       |".format(self.router_id))
        print("+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+")
        print("|   Destination   |   Metric   |    Next Hop    |    Timeout    |    Garbage-timer    |") 
        print("+-------------------------------------------------------------------------------------+")
        for dest_id, values in self.routing_table.items():
            if dest_id == self.router_id:
                continue
            
            elapse1 = 0
            elapse2 = 0
            if values[2] is not None:
                elapse1 = current_time - values[2]
            
            if values[3] is not None:
                elapse2 = current_time - values[3]

            print("        {}               {}              {}               {:.2f}              {:.2f}".format(dest_id, values[0], values[1], elapse1, elapse2))
            print("+-------------------------------------------------------------------------------------+")
        print()
        print()
