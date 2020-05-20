import socket
import threading
import json
import time
from modelSystemType import MetricsValidator
import metrics_messages_pb2
from influxdb import InfluxDBClient
from google.protobuf.json_format import MessageToDict
#https://wiki.python.org/moin/UdpCommunication
#https://medium.com/the-andela-way/machine-monitoring-tool-using-python-from-scratch-8d10411782fd


class Server:
    def __init__(self, init_path_configuration, model_path_validator):

        with open(init_path_configuration, 'r') as json_file:
            self.__config = json.load(json_file)

        print("[*] Configuración del servidor: ")
        print(self.__config)

        self.__model_validator = MetricsValidator(model_path_validator)
        self.__server_ip = self.__config['serverIp']
        self.__buffer_size = self.__config['buffer_size']
        self.__port = self.__config['port']
        self.__secret_password = self.__config['secretPassword']
        self.__allowed_hosts = self.__config['allowedHosts']
        self.__host_connected = []
        self.__server = None

        self.__switcher_message_type = {
            0: self.__close_communication,
            1: self.__treat_data,
            2: self.__send_response
        }

    def start(self):
        self.__server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # TCP
        self.__server.bind((self.__server_ip, self.__port))
        self.__server.listen(5)
        while True:
            print("[*] Esperando mensajes en %s:%d" % (self.__server_ip, self.__port))
            client, addr = self.__server.accept()

            #message = metrics_messages_pb2.Message()
            #message.ParseFromString(data)

            print("[*] Conexión establecida con: %s" % client)
            #method = self.__switcher_message_type.get(message.config.message_type)
            #method(message)
            client.settimeout(60)
            threading.Thread(target=self.listen_to_client, args=(client, addr)).start()

    def listen_to_client(self, client, address):

        connected = True
        while connected:
            data = client.recv(self.__buffer_size)

            message = metrics_messages_pb2.Message()
            message.ParseFromString(data)

            print("[*] Mensaje recibido: %s" % message)
            method = self.__switcher_message_type.get(message.config.message_type)
            if message.config.message_type == 2:
                method(message, client)
            else:
                method(message)
            if message.config.message_type == 0:
                connected = False

    def __send_response(self, message_received, client):
        print(self.__host_connected)
        if message_received.config.Hostname in self.__allowed_hosts:

            if message_received.config.Hostname not in self.__host_connected:

                if message_received.startCommunication.password == self.__secret_password:
                    self.__host_connected.append(message_received.config.Hostname)
                    print("[*] Conexion establecida con %s:%d: %s" % (message_received.config.ip,
                                                                      message_received.config.port,
                                                                      message_received.config.Hostname))

                    message = metrics_messages_pb2.Message()
                    message.ack.response = "OK"
                    client.send(message.SerializeToString())

                    print("[*] Mensaje de confirmación enviado a %s:%d: %s" % (message_received.config.ip,
                                                                               message_received.config.port,
                                                                               message_received.config.Hostname))

                else:
                    print("[*] Conexión interrumpida con %s:%d %s (clave incorrecta)" % (message_received.config.ip,
                                                                                         message_received.config.port,
                                                                                         message_received.config.Hostname))

            else:
                print("[*] Conexión interrumpida con %s:%d %s (ya están conectados)" % (message_received.config.ip,
                                                                                        message_received.config.port,
                                                                                        message_received.config.Hostname))

        else:
            print("[*] Conexion interrumpida con %s:%d %s" % (message_received.config.ip,
                                                              message_received.config.port,
                                                              message_received.config.Hostname))

    def __close_communication(self, message_received):
        if message_received.config.Hostname in self.__host_connected:
            print("[*] Eliminada conexión con %s" % message_received.config.Hostname)
            self.__host_connected.remove(message_received.config.Hostname)
        else:
            print("[*] No existía conexión previamente con %s:%d %s" % (message_received.config.ip,
                                                                        message_received.config.port,
                                                                        message_received.config.Hostname))

    def __treat_data(self, message_received):

        if message_received.config.Hostname in self.__host_connected:
            print("[*]Metricas recogidas: ")
            #Se añade la latencia con el servidor
            message_received.data.metrics.var_latency.clientServer = int(time.time()*1000.0) - int(message_received.data.actualTime)
            print(message_received)
            #metrics = self.__model_validator.verify_metrics(data['message']['SystemMetrics'], data['message']['metrics'])
            print("[*] Métricas validadas del sistema: %s" % message_received.data.SystemMetrics)
            #Ingestar en influx

            client = InfluxDBClient(host='localhost', port=8086, database='metrics')
            print(client.get_list_database())
            if {'name': 'metrics'} not in client.get_list_database():
                client.create_database('metrics')
                client.create_retention_policy("Monthly", "4w", "2", database='metrics')
                client.create_user("admin", "admin1234", admin=True)
            print(client.get_list_measurements())
            points = self.__construct_points(MessageToDict(message_received))
            print(points)
            try:
                print("[*] Ingestando en la BBDD")

                print(client.write_points(points, database='metrics', retention_policy='Monthly', time_precision='ms',
                                          batch_size=20))
            except Exception:
                print("No se ha podido insertar en la base de datos")

        else:
            print("[*] No existía conexión previamente con %s:%d %s" % (message_received.config.ip,
                                                                        message_received.config.port,
                                                                        message_received.config.Hostname))

    def __construct_points(self, message_received):
        points = []
        point = {
            "measurement": '',
            "tags": {
                "hostname": message_received['config']['Hostname'],
                "SystemType": message_received['data']['SystemMetrics']
            },
            "time": int(message_received['data']['actualTime']),
            "fields": ''
        }

        for metric in message_received['data']['metrics']:
            point['measurement'] = metric[3:]
            if type(message_received['data']['metrics'][metric]) == list:
                for elem in message_received['data']['metrics'][metric]:
                    point['fields'] = elem
                    points.append(point.copy())
            else:
                point['fields'] = message_received['data']['metrics'][metric]
                points.append(point.copy())

        return points



if __name__ == '__main__':

    path_configuration = "C:/Users/Javier/PycharmProjects/TFG-Sistema-monitorizacion/server_configuration.json"
    path_model_validator = "C:/Users/Javier/PycharmProjects/TFG-Sistema-monitorizacion/models_validator.json"
    server = Server(path_configuration, path_model_validator)
    server.start()


    #path_configuration = "C:/Users/Javier/PycharmProjects/PruebasTFG/metricData.json"
    #with open(path_configuration, 'r') as json_file:
        #metrics = json.load(json_file)
    #print(metrics)
