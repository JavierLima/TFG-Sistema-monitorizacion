#!/bin/bash
mainDisk=(`df --total | grep 'total'`)
mem=(`free --total | sed "1d"`)
times=(`uptime`)
cpu=(`iostat -c | tail -n 4 | head -n 1`)
ioRatio=(`iostat -d | grep "sda"`)
cpusUsageNumber=`lscpu --extended -b | sed "1d" | wc -l`
cpusTotalNumber=`nproc --all`
#!logs=`cat /var/log/syslog`
disks=(`df -T | sed "1d"`)
disksEntries=`df -T | sed "1d" | wc -l`
temperature=`echo $(((RANDOM%11)+27))`
processesTable=(`ps -e -o pcpu,pid,pmem,nice,state,group,user,start,cputime,args --sort pcpu | sed -e 's/$/ .endline/' | sed '/^ 0.0 /d' | sed "1d"`)
processesTableEntries=`ps -e -o pcpu,pid,pmem,nice,state,group,user,start,cputime,args --sort pcpu | sed '/^ 0.0 /d' | sed "1d" | wc -l`
activeProcessesNumber=`ps -a | wc -l`
totalProcessesNumber=`ps -ax | wc -l`
networkCards=(`ifconfig`)
latency=`ping 127.0.0.1 -c 3 | tail -n 2`
latencyPackageStadistics=($latency)
minRTT=`echo $latency | grep rtt | awk -F '/' '{print $4}' | cut -d '=' -f 2 | tr -d ' '`
meanRTT=`echo $latency | grep rtt | awk -F'/' '{print $5}'`
maxRTT=`echo $latency | grep rtt | awk -F'/' '{print $6}'`
mdevRTT=`echo $latency | grep rtt | awk -F '/' '{print $7}' | cut -d ' ' -f 1 | tr -d ' '`
host=`hostname`

#!echo -e "-- Logs --\r\n$logs\r\n\r\n"

countEntries=0
partitions='['
iterator=0
while [ $countEntries -lt $disksEntries ];do
	for e in 0 1 2 3 4 5 6;
	do
		case "$e" in 0)
			partitions=''${partitions}'{"identificatorName":"'${disks[$iterator]}'",'
		;;
		1)
                        partitions=''${partitions}' "type":"'${disks[$iterator]}'",'
                ;;
		2)
                        partitions=''${partitions}' "totalDisk":'${disks[$iterator]}','
                ;;
		3)
                        partitions=''${partitions}' "usedDisk":'${disks[$iterator]}','
                ;;
		4)
                        partitions=''${partitions}' "freeDisk":'${disks[$iterator]}','
                ;;
		5)
                        partitions=''${partitions}' "usagePercentDisk":"'${disks[$iterator]%\%}'",'
                ;;
		6)
                        partitions=''${partitions}' "mountPoint":"'${disks[$iterator]}'"},'
                ;;
		*)
			echo "ERROR: La métrica partitions no dispone de tantos parámetros"
		;;
		esac
		((iterator++))
	done;
	((countEntries++))
done;
partitions="${partitions:0:-1}"
partitions="${partitions}]"


countEntries=0
process='['
iterator=0
while [ $countEntries -lt $processesTableEntries ];do
        for e in 0 1 2 3 4 5 6 7 8 9;
        do
                case "$e" in 0)
                        process=''${process}'{"usedPercentageCpu":'${processesTable[$iterator]}','
                ;;
                1)
                        process=''${process}' "pid":'${processesTable[$iterator]}','
                ;;
                2)
                        process=''${process}' "usedPercentageMem":'${processesTable[$iterator]}','
                ;;
                3)
                        process=''${process}' "nice":'${processesTable[$iterator]}','
                ;;
                4)
                        process=''${process}' "group":"'${processesTable[$iterator]}'",'
                ;;
                5)
                        process=''${process}' "user":"'${processesTable[$iterator]}'",'
                ;;
                6)
                        process=''${process}' "state":"'${processesTable[$iterator]}'",'
                ;;
                7)
			if [ ${#processesTable[$iterator]} -lt 8 ]
                        then
				process=''${process}' "start":"'${processesTable[$iterator]}''
				((iterator++))
				process=''${process}' '${processesTable[$iterator]}'",'
			else
				process=''${process}' "start":"'${processesTable[$iterator]}'",'
			fi
                ;;
                8)
                        process=''${process}' "cpuTime":"'${processesTable[$iterator]}'",'
                ;;
                9)
			process=''${process}' "command":"'
			while [ ${processesTable[$iterator]} != ".endline" ];do
                        	process=''${process}''${processesTable[$iterator]}' '
				((iterator++))
			done;
			process="${process:0:-1}"
			process=''${process}'"},'
                ;;
                *)
                        echo "ERROR: La métrica process no dispone de tantos parámetros"
                ;;
                esac
                ((iterator++))
        done;
        ((countEntries++))
done;
process="${process:0:-1}"
process="${process}]"



countEntries=0
iterator=0
networkMetrics='[{"networkCardName":"'${networkCards[$iterator]%\:}'",'
while [ ${networkCards[$iterator]} != "lo:" ];do

	case ${networkCards[$iterator]} in "mtu")
		((iterator++))
        	networkMetrics=''${networkMetrics}' "MTU":'${networkCards[$iterator]}','
        ;;
        "inet")
                ((iterator++))
                networkMetrics=''${networkMetrics}' "IP":"'${networkCards[$iterator]}'",'
        ;;
        "netmask")
		((iterator++))
                networkMetrics=''${networkMetrics}' "netMask":"'${networkCards[$iterator]}'",'
        ;;
	"broadcast")
		((iterator++))
		networkMetrics=''${networkMetrics}' "broadcastAddress":"'${networkCards[$iterator]}'",'
	;;
	"inet6")
		((iterator++))
                networkMetrics=''${networkMetrics}' "IPv6Address":"'${networkCards[$iterator]}'",'
        ;;
	"ether")
		((iterator++))
                networkMetrics=''${networkMetrics}' "MACAddress":"'${networkCards[$iterator]}'",'
        ;;
        "txqueuelen")
		((iterator++))
                networkMetrics=''${networkMetrics}' "txQueueLen":'${networkCards[$iterator]}','
		((iterator++))
                networkMetrics=''${networkMetrics}' "connectionProtocol":"'${networkCards[$iterator]}'",'
        ;;
        "RX")
		((iterator++))
		((iterator++))
                networkMetrics=''${networkMetrics}' "RXPackages":'${networkCards[$iterator]}','
		((iterator++))
		((iterator++))
		((iterator++))
		((iterator++))
		((iterator++))
		((iterator++))
		((iterator++))
		networkMetrics=''${networkMetrics}' "RXErrors":'${networkCards[$iterator]}','
        ;;
        "TX")
		((iterator++))
		((iterator++))
                networkMetrics=''${networkMetrics}' "TXPackages":'${networkCards[$iterator]}','
                ((iterator++))
                ((iterator++))
                ((iterator++))
                ((iterator++))
                ((iterator++))
                ((iterator++))
                ((iterator++))
                networkMetrics=''${networkMetrics}' "TXErrors":'${networkCards[$iterator]}','
        ;;
	"collisions")
		((iterator++))
                networkMetrics=''${networkMetrics}' "collisions":'${networkCards[$iterator]}'},'
                ((iterator++))
		if [ ${networkCards[$iterator]} != "lo:" ]
        	then
                	networkMetrics=''${networkMetrics}'{"networkCardName":"'${networkCards[$iterator]%\:}'", '
        	fi
        ;;
        *)
               	((iterator++))
        ;;
        esac
done;
networkMetrics="${networkMetrics:0:-1}"
networkMetrics="${networkMetrics}]"

jsonData='{"Hostname":"'$host'", "SystemMetrics":"LinuxDebian", "actualTime":"'${times[0]}'", "metrics":{ '\
'"latency":{"minRTT":'$minRTT', "meanRTT":'$meanRTT', "maxRTT":'$maxRTT', "mdevRTT":'$mdevRTT', "packageTransmited":'${latencyPackageStadistics[0]}', '\
'"packageReceived":'${latencyPackageStadistics[3]}',"packageLossPercentage":'${latencyPackageStadistics[5]%\%}', "timeRequest":'${latencyPackageStadistics[9]%\ms}'}, '\
'"cpu":{"userPercentage":"'${cpu[0]}'", "nicePercentage":"'${cpu[1]}'", "systemPercentage":"'${cpu[2]}'", "iowaitPercentage":"'${cpu[3]}'", "stealPercentage":"'${cpu[4]}'", '\
'"idlePercentage":"'${cpu[5]}'"}, '\
'"cpusNumber":{"cpusTotalNumber":'$cpusTotalNumber', "cpusUsageNumber":'$cpusUsageNumber'}, '\
'"ioRatio":{"deviceName":"'${ioRatio[0]}'", "transfersPerSecond":"'${ioRatio[1]}'", "kilobytesReadsPerSecond":"'${ioRatio[2]}'", "kilobytesWrittenPerSecond":"'${ioRatio[3]}'", '\
'"kilobytesRead":'${ioRatio[4]}', "kilobytesWritten":'${ioRatio[5]}'}, '\
'"disk":{"identificatorName":"'${mainDisk[0]}'", "totalDisk":'${mainDisk[1]}', "usedDisk":'${mainDisk[2]}', "freeDisk":'${mainDisk[3]}', "usagePercentDisk":'${mainDisk[4]%\%}'}, '\
'"temperature":{"degrees":'${temperature}'}, '\
'"partitions":'$partitions', '\
'"process":'$process', '\
'"processesNumber":{"activeProcessesNumber":'$activeProcessesNumber', "totalProcessesNumber":'$totalProcessesNumber'}, '\
'"mem":{"totalMem":'${mem[1]}', "usedMem":'${mem[2]}', "freeMem":'${mem[3]}', "sharedMem":'${mem[4]}', "buffersMem":'${mem[5]}', "cachedMem":'${mem[6]}', "swapTotalMem":'${mem[8]}', '\
'"swapUsedMem":'${mem[9]}', "swapFreeMem":'${mem[10]}', "totalRAM":'${mem[12]}', "usedRAM":'${mem[13]}', "freeRAM":'${mem[14]}'}, '\
'"systemAdditionalInfo":{"systemRunningTime":"'${times[1]}' '${times[2]}' '${times[3]}' '${times[4]%\,}'", "usersLoggedOnNumber":'${times[5]}', "systemLoadAverage1M":"'${times[9]%\,}'", '\
'"systemLoadAverage5M":"'${times[10]%\,}'", "systemLoadAverage15M":"'${times[11]}'"}, '\
'"networkMetrics":'$networkMetrics'}}'

echo $jsonData
echo $jsonData | jq . >> metricsData.json

