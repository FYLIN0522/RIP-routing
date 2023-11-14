from socket import *
from router import *
import select
import sys



def configureFile(filename):
    """ Read the configure file"""
    file = open(filename, 'r')
    lines = file.readlines()
    routers = {}
    router_id, input_ports, output_ports, timer = None, None, None, None
    
    for line in lines:
        line = line.split()
        head, data = line[0], line[1]
        

        if head == "router-id":
            router_id = int(data)
            if router_id < 1 or router_id > 64000:
                raise ValueError('Invalid router id: {}'.format(router_id))


        elif head == "input-ports":
            input_ports = data.split(',')

            port_check = []
            for port_str in input_ports:
                port = int(port_str)
                if port < 1024 or port > 64000:
                    raise ValueError('Invalid port number: {}'.format(port))
                if port in port_check:
                    raise ValueError('Port numbers must be unique: {}'.format(port))
                port_check.append(port)
                
            input_ports = port_check
            
                          
        elif head == "outputs":
            outputs = data.split(',')


        elif head == "timer":
            timer = int(data)
            if timer < 0 or timer > 30:
                raise ValueError("Timer must be between 1 and 30.")        


    if router_id == None:
        raise ValueError("No Router ID given")
    if input_ports == None: 
        raise ValueError("No input ports given")
    if outputs == None: 
        raise ValueError("No output ports given")

    
    if router_id in routers.keys():
        raise ValueError("Each router must be unique")
       
    return router_id, input_ports, outputs, timer
                     

def create_socket(router):
    """ Takes sockets and port numbers """
    socket_list = []
    
    for port in router.input_port:
        try:
            s = socket(AF_INET, SOCK_DGRAM)

        except:
            print('socket error')
            sys.exit()

        try:
            s.bind(("127.0.0.1", port))

        except:
            print('bind error')
            sys.exit()

        socket_list.append(s)

    return socket_list


def main():
    if len(sys.argv) < 2:
        print('No file readed')
        sys.exit()

    filename = sys.argv[1]
    router_id, input_ports, outputs, timer = configureFile(filename)


    if timer is None:
        router = Router(router_id, input_ports, outputs)

    else:
        router = Router(router_id, input_ports, outputs, timer)

    
    
    inputs = create_socket(router)
    outputs = []


    print('Routing start')
    router.timer_start()
    
    while True:
        router.print_routing_table()
        router.check_timer_expire()
        readable, writable, exceptional = select.select(inputs, outputs, inputs, 1)
        
        if readable:
            for socket in readable:
                data, addr = socket.recvfrom(1024)
                router.unpack_recieve_packet(data)

            

main()


