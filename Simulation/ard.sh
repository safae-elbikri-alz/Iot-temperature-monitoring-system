count=1

while true
do
        tmp1=$(shuf -i 22-29 -n 1)
        hum1=$(shuf -i 65-70 -n 1)
	tmp2=$(shuf -i 22-29 -n 1)
        hum2=$(shuf -i 65-70 -n 1)
	tmp3=$(shuf -i 22-29 -n 1)
        hum3=$(shuf -i 65-70 -n 1)
	echo $tmp1 " and " $tmp2 " and " $tmp3  
	n=$(shuf -i 2-5 -n 1)
	i=0
	while [ $i -lt $n ]
	do
		echo "PUBLISHING $count"
		mosquitto_pub -m $(printf '{"temperature":%d,"humidity":%d}' "$tmp1" "$hum1") -t "//esp8266\1\dhtreadings" -h mqtt.eclipse.org
		mosquitto_pub -m $(printf '{"temperature":%d,"humidity":%d}' "$tmp2" "$hum2") -t "//esp8266\2\dhtreadings" -h mqtt.eclipse.org
		mosquitto_pub -m $(printf '{"temperature":%d,"humidity":%d}' "$tmp3" "$hum3") -t "//esp8266\3\dhtreadings" -h mqtt.eclipse.org
		echo "success"
		i=$[$i+1]
		count=$[$count+1]
		sleep 1
	done
	count=$[$count+1]
done

echo $message
