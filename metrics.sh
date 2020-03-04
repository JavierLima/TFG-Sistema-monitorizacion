
#!/bin/bash
mainDisk=`df --total | grep 'total'`
mem=`free --total`
times=`uptime`
cpu=`iostat -c`
ioRatio=`iostat -d | grep "sda"`
cpusUsageNumber=`lscpu --extended -c | wc -l`
cpusTotalNumber=`nproc --all`
logs=`cat /var/log/syslog`
disks=`df -T`
temperature=`echo $(((RANDOM%11)+27))`
processesTable=`ps -e -o pcpu,pid,pmem,nice,state,group,user,start,cputime,args --sort pcpu | sed '/^ 0.0 /d'`
activeProcessesNumber=`ps -a | wc -l`
totalProcessesNumber=`ps -ax | wc -l`
redTargets=`ifconfig`
latency=`ping 127.0.0.1 -c 3 | grep rtt`
host=`hostname`

echo -e "-- Logs --\r\n$logs\r\n\r\n"
echo -e "-- Tiempo --\r\n$times\r\n\r\n"
echo -e "-- Disco total --\r\n$mainDisk\r\n\r\n"
echo -e "-- Memoria --\r\n$mem\r\n\r\n"
echo -e "-- Discos --\r\n$disks\r\n\r\n"
echo -e "-- IO Disk ratio --\r\n$ioRatio\r\n\r\n"
echo -e "-- Temperatura --\r\nTemp:    $temperatureºC\r\n\r\n"
echo -e "-- Número de procesos --\r\nActivos: $activeProcessesNumber\r\nTotales: $totalProcessesNumber\r\n"
echo -e "-- Tabla de procesos --\r\n$processesTable\r\n\r\n"
echo -e "-- Tarjetas de red --\r\n$redTargets\r\n\r\n"
echo -e "-- Latencia --\r\n$latency\r\n\r\n"
echo -e "-- Hostname --\r\n$host\r\n\r\n"
echo -e "-- CPU --\r\n$cpu\r\nNúmero total de cpus: $cpusTotalNumber\r\nNúmero de cpus en uso: $cpusUsageNumber"

