import socket
import json
import time
import os
import metrics_messages_pb2


class Client:
    def __init__(self, init_path):

        with open(init_path, 'r') as json_file:
            self.__config = json.load(json_file)
        print("[*] Configuración del cliente: ")
        print(self.__config)
        self.__server_ip = self.__config['serverIp']
        self.__client_ip = self.__config['clientIp']
        self.__port = self.__config['port']
        self.__buffer_size = self.__config['buffer_size']
        self.__system_client = self.__config['systemClient']
        self.__system_metrics = self.__config['systemMetrics']
        self.__init_message = self.__config['initMessage']
        self.__metrics_json_path = self.__config['metricsJsonPath']
        self.__connected = False
        self.__client = None
        self.__hostname = socket.gethostname()
        self.__client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect_server(self):

        if not self.__connected:
            self.__start_communication()

            response = self.__get_server_response()
            if response.ack.response == "OK":
                self.__send_metrics()
            else:
                print("[*] Error de conexión %s:%d" % (self.__server_ip, self.__port))
        else:
            self.__send_metrics()

        self.__close_communication()

    def __start_communication(self):
        print("[*] Estableciendo conexion con %s:%d" % (self.__server_ip, self.__port))
        self.__client.connect((self.__server_ip, self.__port))

        message = metrics_messages_pb2.Message()
        message.config.Hostname = self.__hostname
        message.config.message_type = metrics_messages_pb2.Config.START_COMMUNICATION
        message.config.ip = self.__client_ip
        message.config.port = self.__port
        message.startCommunication.password = self.__init_message

        self.__client.sendall(message.SerializeToString())

        self.__connected = True

    def __close_communication(self):
        print("[*] Finalizando conexion con %s:%d" % (self.__server_ip, self.__port))

        message = metrics_messages_pb2.Message()
        print(self.__hostname)
        message.config.Hostname = self.__hostname
        message.config.message_type = metrics_messages_pb2.Config.CLOSE_COMMUNICATION
        message.config.ip = self.__client_ip
        message.config.port = self.__port

        self.__client.sendall(message.SerializeToString())

        self.__client.close()
        self.__connected = False

    def __get_server_response(self):
        print("[*] Recibiendo respuesta del %s:%d" % (self.__server_ip, self.__port))

        data = self.__client.recv(self.__buffer_size)

        message = metrics_messages_pb2.Message()
        message.ParseFromString(data)

        return message

    def __send_metrics(self):
        print("[*] Enviando metricas con %s:%d" % (self.__server_ip, self.__port))
        os.system("./metrics.sh")
        time.sleep(3)
        with open(self.__metrics_json_path, 'r') as json_file:
            metrics = json.load(json_file)

        message = metrics_messages_pb2.Message()
        message.config.Hostname = self.__hostname
        message.config.message_type = metrics_messages_pb2.Config.METRICS
        message.config.ip = self.__client_ip
        message.config.port = self.__port
        message = self.__set_protobuffer_message(message, metrics)
        print(len(message.SerializeToString()))
        print(message.SerializeToString())

        self.__client.sendall(message.SerializeToString())
        time.sleep(5)

    def __set_protobuffer_message(self, message, metrics):
        """
        Esta funcion se encarga de setear un mensaje de tipo protobuffer con las metricas obtenidas de un json, este mensaje esta definido
        en el archivo metrics_messages.proto. Solo admite ese formato, es decir, en el caso que se quieran obtener metricas de otro tipo de sistema,
        es necesario que el otro sistema al generar el json utilice los nombres definidos de ese archivo.

        :param message: Un mensaje de tipo protobuffer
        :param metrics: Metricas a setear para el mensaje utilizado por protobuffer
        :return message: El mensaje de tipo protobuffer seteado con las caracteristicas de las métricas obtenidas de un json
        """
        message.data.SystemMetrics = metrics['SystemMetrics']
        message.data.actualTime = metrics['actualTime']

        message.data.metrics.var_latency.minRTT = metrics['metrics']['latency']['minRTT']
        message.data.metrics.var_latency.meanRTT = metrics['metrics']['latency']['meanRTT']
        message.data.metrics.var_latency.maxRTT = metrics['metrics']['latency']['maxRTT']
        message.data.metrics.var_latency.mdevRTT = metrics['metrics']['latency']['mdevRTT']
        message.data.metrics.var_latency.packageTransmited = metrics['metrics']['latency']['packageTransmited']
        message.data.metrics.var_latency.packageReceived = metrics['metrics']['latency']['packageReceived']
        message.data.metrics.var_latency.packageLossPercentage = metrics['metrics']['latency']['packageLossPercentage']
        message.data.metrics.var_latency.timeRequest = metrics['metrics']['latency']['timeRequest']

        message.data.metrics.var_cpu.userPercentage = metrics['metrics']['cpu']['userPercentage']
        message.data.metrics.var_cpu.nicePercentage = metrics['metrics']['cpu']['nicePercentage']
        message.data.metrics.var_cpu.systemPercentage = metrics['metrics']['cpu']['systemPercentage']
        message.data.metrics.var_cpu.iowaitPercentage = metrics['metrics']['cpu']['iowaitPercentage']
        message.data.metrics.var_cpu.stealPercentage = metrics['metrics']['cpu']['stealPercentage']
        message.data.metrics.var_cpu.idlePercentage = metrics['metrics']['cpu']['idlePercentage']

        message.data.metrics.var_cpusNumber.cpusTotalNumber = metrics['metrics']['cpusNumber']['cpusTotalNumber']
        message.data.metrics.var_cpusNumber.cpusUsageNumber = metrics['metrics']['cpusNumber']['cpusUsageNumber']

        message.data.metrics.var_ioRatio.deviceName = metrics['metrics']['ioRatio']['deviceName']
        message.data.metrics.var_ioRatio.transfersPerSecond = metrics['metrics']['ioRatio']['transfersPerSecond']
        message.data.metrics.var_ioRatio.kilobytesReadsPerSecond = metrics['metrics']['ioRatio']['kilobytesReadsPerSecond']
        message.data.metrics.var_ioRatio.kilobytesWrittenPerSecond = metrics['metrics']['ioRatio']['kilobytesWrittenPerSecond']
        message.data.metrics.var_ioRatio.kilobytesRead = metrics['metrics']['ioRatio']['kilobytesRead']
        message.data.metrics.var_ioRatio.kilobytesWritten = metrics['metrics']['ioRatio']['kilobytesWritten']

        message.data.metrics.var_disk.identificatorName = metrics['metrics']['disk']['identificatorName']
        message.data.metrics.var_disk.totalDisk = metrics['metrics']['disk']['totalDisk']
        message.data.metrics.var_disk.usedDisk = metrics['metrics']['disk']['usedDisk']
        message.data.metrics.var_disk.freeDisk = metrics['metrics']['disk']['freeDisk']
        message.data.metrics.var_disk.usagePercentDisk = metrics['metrics']['disk']['usagePercentDisk']

        message.data.metrics.var_temperature.degrees = metrics['metrics']['temperature']['degrees']

        for elem in metrics['metrics']['partitions']:
            partitions = message.data.metrics.var_partitions.add()
            partitions.identificatorName = elem['identificatorName']
            partitions.type = elem['type']
            partitions.totalDisk = elem['totalDisk']
            partitions.usedDisk = elem['usedDisk']
            partitions.freeDisk = elem['freeDisk']
            partitions.usagePercentDisk = elem['usagePercentDisk']
            partitions.mountPoint = elem['mountPoint']

        for elem in metrics['metrics']['process']:
            process = message.data.metrics.var_process.add()
            process.usedPercentageCpu = elem['usedPercentageCpu']
            process.pid = elem['pid']
            process.usedPercentageMem = elem['usedPercentageMem']
            process.nice = elem['nice']
            process.group = elem['group']
            process.user = elem['user']
            process.state = elem['state']
            process.start = elem['start']
            process.cpuTime = elem['cpuTime']
            process.command = elem['command']

        message.data.metrics.var_processesNumber.activeProcessesNumber = metrics['metrics']['processesNumber']['activeProcessesNumber']
        message.data.metrics.var_processesNumber.totalProcessesNumber = metrics['metrics']['processesNumber']['totalProcessesNumber']

        message.data.metrics.var_mem.totalMem = metrics['metrics']['mem']['totalMem']
        message.data.metrics.var_mem.usedMem = metrics['metrics']['mem']['usedMem']
        message.data.metrics.var_mem.freeMem = metrics['metrics']['mem']['freeMem']
        message.data.metrics.var_mem.sharedMem = metrics['metrics']['mem']['sharedMem']
        message.data.metrics.var_mem.buffersMem = metrics['metrics']['mem']['buffersMem']
        message.data.metrics.var_mem.cachedMem = metrics['metrics']['mem']['cachedMem']
        message.data.metrics.var_mem.swapTotalMem = metrics['metrics']['mem']['swapTotalMem']
        message.data.metrics.var_mem.swapUsedMem = metrics['metrics']['mem']['swapUsedMem']
        message.data.metrics.var_mem.swapFreeMem = metrics['metrics']['mem']['swapFreeMem']
        message.data.metrics.var_mem.totalRAM = metrics['metrics']['mem']['totalRAM']
        message.data.metrics.var_mem.usedRAM = metrics['metrics']['mem']['usedRAM']
        message.data.metrics.var_mem.freeRAM = metrics['metrics']['mem']['freeRAM']

        message.data.metrics.var_systemAdditionalInfo.systemRunningTime = metrics['metrics']['systemAdditionalInfo']['systemRunningTime']
        message.data.metrics.var_systemAdditionalInfo.usersLoggedOnNumber = metrics['metrics']['systemAdditionalInfo']['usersLoggedOnNumber']
        message.data.metrics.var_systemAdditionalInfo.systemLoadAverage1M = metrics['metrics']['systemAdditionalInfo']['systemLoadAverage1M']
        message.data.metrics.var_systemAdditionalInfo.systemLoadAverage5M = metrics['metrics']['systemAdditionalInfo']['systemLoadAverage5M']
        message.data.metrics.var_systemAdditionalInfo.systemLoadAverage15M = metrics['metrics']['systemAdditionalInfo']['systemLoadAverage15M']

        for elem in metrics['metrics']['networkMetrics']:
            networkMetric = message.data.metrics.var_networkMetrics.add()
            networkMetric.networkCardName = elem['networkCardName']
            networkMetric.MTU = elem['MTU']
            networkMetric.IP = elem['IP']
            networkMetric.netMask = elem['netMask']
            networkMetric.broadcastAddress = elem['broadcastAddress']
            #networkMetric.IPv6Address = elem['IPv6Address']
            networkMetric.MACAddress = elem['MACAddress']
            networkMetric.txQueueLen = elem['txQueueLen']
            networkMetric.connectionProtocol = elem['connectionProtocol']
            networkMetric.RXPackages = elem['RXPackages']
            networkMetric.RXErrors = elem['RXErrors']
            networkMetric.TXPackages = elem['TXPackages']
            networkMetric.TXErrors = elem['TXErrors']
            networkMetric.collisions = elem['collisions']

        return message

if __name__ == '__main__':

    path = "/client_cron_metrics/client_configuration.json"
    client = Client(path)
    client.connect_server()

