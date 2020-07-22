import socket
import threading
import json
import time
from modelSystemType import MetricsValidator
import metrics_messages_pb2
from influxdb import InfluxDBClient
from google.protobuf.json_format import MessageToDict
import logging
from datetime import datetime
#https://wiki.python.org/moin/UdpCommunication
#https://medium.com/the-andela-way/machine-monitoring-tool-using-python-from-scratch-8d10411782fd


lock = threading.Lock()
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

        self.__logger = logging.getLogger(self.__config["logging"]["name"])
        self.__logger.setLevel(logging.DEBUG)  # logging.WARNING
        formatter = logging.Formatter(self.__config["logging"]["format"])

        # Add a console handler
        log_ch = logging.StreamHandler()
        log_ch.setLevel(logging.ERROR)
        log_ch.setFormatter(formatter)

        # Add file log handler
        log_fh = logging.FileHandler('SystemMetrics_Server.log')
        log_fh.setLevel(logging.DEBUG)
        log_fh.setFormatter(formatter)

        self.__logger.addHandler(log_ch)
        self.__logger.addHandler(log_fh)
        self.__host_connected = []
        self.__server = None

        self.__switcher_message_type = {
            0: self.__close_communication,
            1: self.__treat_data,
            2: self.__send_response
        }

    def start(self):
        self.__logger.info('[*] Iniciando el servidor: ')

        self.__server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # TCP
        self.__server.bind((self.__server_ip, self.__port))
        self.__server.listen(5)
        while True:
            t = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.__logger.info('[*] Esperando mensajes en ' + self.__server_ip + ':' + str(self.__port))
            client, addr = self.__server.accept()

            self.__logger.info('[*] Conexión establecida con: {}'.format(client))

            client.settimeout(120)
            threading.Thread(target=self.listen_to_client, args=(client, addr)).start()

    def listen_to_client(self, client, address):

        connected = True
        while connected:
            data = client.recv(self.__buffer_size)
            if data:
                message = metrics_messages_pb2.Message()
                message.ParseFromString(data)
                print("Mensaje recibido")
                print(message)
                self.__logger.info('[*] Mensaje recibido: {}'.format(message))
                method = self.__switcher_message_type.get(message.config.message_type)
                if message.config.message_type == 2:

                    method(message, client)
                else:
                    method(message)
                if message.config.message_type == 0:
                    connected = False

    def __send_response(self, message_received, client):
        global lock
        if message_received.config.Hostname in self.__allowed_hosts:
            lock.acquire()
            if message_received.config.Hostname not in self.__host_connected:
                if message_received.startCommunication.password == self.__secret_password:
                    self.__host_connected.append(message_received.config.Hostname)
                    lock.release()

                    self.__logger.info('[*] Conexion establecida con ' + message_received.config.ip + ':' +
                                        str(message_received.config.port) + ', ' + message_received.config.Hostname)

                    message = metrics_messages_pb2.Message()
                    message.ack.response = "OK"
                    time.sleep(3)
                    client.send(message.SerializeToString())
                    self.__logger.info('[*] Mensaje de confirmación enviado a ' + message_received.config.ip + ':' +
                                        str(message_received.config.port) + ', ' + message_received.config.Hostname)

                else:
                    self.__logger.error('[*] Conexion interrumpida con ' + message_received.config.ip + ':' +
                                        str(message_received.config.port) + ', ' + message_received.config.Hostname + ' Clave de seguridad incorrecta')

            else:
                lock.release()
                self.__logger.error('[*] Conexion interrumpida con ' + message_received.config.ip + ':' +
                                    str(message_received.config.port) + ', ' + message_received.config.Hostname + ' Ya están conectados')
                lock.acquire()
                self.__host_connected.remove(message_received.config.Hostname)
                lock.release()

        else:
            self.__logger.error('[*] Conexion interrumpida con ' + message_received.config.ip + ':'+
                                str(message_received.config.port) + ', ' + message_received.config.Hostname + ' Host no permitido')

    def __close_communication(self, message_received):
        global lock
        lock.acquire()
        if message_received.config.Hostname in self.__host_connected:
            lock.release()

            self.__logger.info('[*] Eliminada conexión con: {}'.format(message_received.config.Hostname))

            lock.acquire()
            self.__host_connected.remove(message_received.config.Hostname)
            lock.release()
        else:
            lock.release()
            self.__logger.error('[*] No existía conexión previamente con ' + message_received.config.ip + ':' +
                                str(message_received.config.port) + ', ' + message_received.config.Hostname)

    def __treat_data(self, message_received):
        global lock
        lock.acquire()
        if message_received.config.Hostname in self.__host_connected:
            lock.release()

            #Se añade la latencia con el servidor
            message_received.data.metrics.var_latency.clientServer = int(time.time()*1000.0) - int(message_received.data.actualTime)
            self.__logger.info('[*] Métricas recogidas: {}'.format(message_received))
            #metrics = self.__model_validator.verify_metrics(data['message']['SystemMetrics'], data['message']['metrics'])
            self.__logger.info('[*] Métricas validadas del sistema: {}'.format(message_received.data.SystemMetrics))
            #Ingestar en influx

            client = InfluxDBClient(host='localhost', port=8086, database='metrics')
            if {'name': 'metrics'} not in client.get_list_database():
                client.create_database('metrics')
                client.create_retention_policy("Monthly", "4w", "2", database='metrics')
                client.create_user("admin", "admin1234", admin=True)
            points = self.__construct_points(MessageToDict(message_received))
            try:
                self.__logger.info('[*] Ingestando en la BBDD')

                print(client.write_points(points, database='metrics', retention_policy='Monthly', time_precision='ms',
                                          batch_size=20))

                self.__logger.info('[*] Se ha ingestado en la BBDD')
                print('[*] Se ha ingestado en la BBDD ' + message_received.config.Hostname)
            except Exception:
                self.__logger.error('[*] No se ha podido insertar en la base de datos')

        else:
            lock.release()
            self.__logger.error('[*] No existía conexión previamente con ' + message_received.config.ip + ':'+
                                str(message_received.config.port) + ', ' + message_received.config.Hostname)

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

    path_configuration = "C:/Users/Javier/PycharmProjects/PruebasTFG/server_configuration.json"
    path_model_validator = "C:/Users/Javier/PycharmProjects/PruebasTFG/models_validator.json"
    server = Server(path_configuration, path_model_validator)
    server.start()
