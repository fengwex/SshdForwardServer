# -*- coding: utf-8 -*-
from socket import *
import threading
import Queue

# test in python 2.7

# a list of local port mapped to machine
#host 跳转机的地址
#port 跳转机的端口
#ip 目标机器的地址
ssh_server_list = [{"host": '10.107.69.84', "port": 10218, "ip": "10.199.169.218"}]

# sync all the threads in each of tunnel
running_flag = []

# receive buffSize
buffer_size = 2048


def get_data_from_ssh_server(rev_msg, tcp_socket, flag):
    """
    :param rev_msg: a queue buffer of message need to be send to SSH client
    :param tcp_socket: instance of socket used for sending data
    :param flag: control this function
    :return: null
    """
    while running_flag[flag]:
        data = tcp_socket.recv(buffer_size)
        if len(data):
            rev_msg.put(str(data))
        else:
            running_flag[flag] = False


def send_data_to_ssh_client(rev_msg, tcp_socket, flag):
    """
    :param rev_msg: a queue buffer of message need to be send to SSH client
    :param tcp_socket: instance of socket used for sending data
    :param flag: control this function
    :return: null
    """
    while running_flag[flag]:
        try:
            data = rev_msg.get(timeout=10)
            data = tcp_socket.send(str(data))
        except:
            pass


def get_data_from_ssh_client(send_msg, tcp_socket, flag):
    """
    :param send_msg: a queue buffer of message need to be send to SSH server in each machine
    :param tcp_socket: instance of socket used for sending data
    :param flag: control this function
    :return: null
    """
    while running_flag[flag]:
        data = tcp_socket.recv(buffer_size)
        if len(data):
            send_msg.put(str(data))
        else:
            running_flag[flag] = False


def send_data_to_ssh_server(send_msg, tcp_socket, flag):
    """
    :param send_msg: a queue buffer of message need to be send to SSH server in each machine
    :param tcp_socket: instance of socket used for sending data
    :param flag: control this function
    :return: null
    """
    while running_flag[flag]:
        try:
            data = send_msg.get(timeout=10)
            data = tcp_socket.send(str(data))
        except:
            pass


def handle_connections(host, ip, port):
    """
    :param host: local ip
    :param ip: which machine the data will be forwarded
    :param port: local port
    :return: null
    """
    ssh_client_socket = socket(AF_INET, SOCK_STREAM)
    ssh_client_socket.bind((host, port))

    # listen 10 client
    ssh_client_socket.listen(10)
    while True:
        ssh_client_side, address = ssh_client_socket.accept()

        # two queue for keeping data from SSH client and SSH server
        buffer_send = Queue.Queue()
        buffer_rev = Queue.Queue()

        ssh_server_side = socket(AF_INET, SOCK_STREAM)
        ssh_server_side.connect((ip, 22))

        flag = True

        running_flag.append(flag)

        rev1 = threading.Thread(target=get_data_from_ssh_server,
                                args=(buffer_rev, ssh_server_side, len(running_flag) - 1))
        rev2 = threading.Thread(target=send_data_to_ssh_client,
                                args=(buffer_rev, ssh_client_side, len(running_flag) - 1))

        send1 = threading.Thread(target=get_data_from_ssh_client,
                                 args=(buffer_send, ssh_client_side, len(running_flag) - 1))
        send2 = threading.Thread(target=send_data_to_ssh_server,
                                 args=(buffer_send, ssh_server_side, len(running_flag) - 1))

        rev1.start()
        rev2.start()
        send1.start()
        send2.start()

if __name__ == "__main__":
    print("start SSH forward server")

    thread_pool = []
    for i in ssh_server_list:
        print("ssh mapping " + i["host"] + ":" + str(i["port"]) + " => " + i["ip"] + ":22")
        t = threading.Thread(target=handle_connections, args=(i["host"], i["ip"], i["port"]))
        thread_pool.append(t)
        t.start()
    print("initialize SSH forward server done")