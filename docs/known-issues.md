# Known issues

## Grafana fails to start with "can't create directory '/var/lib/grafana/whatever' permission denied"

The file permissions on "config/grafana/lib/" may be incorrect. You can fix this by changing the file owner to root, or by giving all users write permission, on all files under that directory. To give all users write permissions on the appropriate files, from the repository root:

```chmod -Rv a+w config/grafana/lib```

## GoFlow2 restarts repeatedly shortly after "docker compose up"

This happens because GoFlow2 needs to send data to Apache Kafka, however, the kafka container takes a fair bit of time to start (usually around 15-20 seconds), so the goflow2 container will try to connect and end up erroring out. The goflow2 container is set to always restart if it dies, so once kafka is ready goflow2 will connect and should work fine. Just wait around 20 seconds after bringing up the docker compose setup. Seeing 5-6 error messages near the start of goflow2's docker logs mentioning 'connection refused for kafka transport' is normal.

## Permission denied while trying to connect to Docker socket

Docker needs root permissions, so you need to do 'docker compose up' as root, or use sudo.

## NetFlow 'template_not_found' errors

This generally happens because the application was restarted and needs to reacquire NetFlowv9 templates. OpenWRT's softflowd periodically sends templates, but there is a substantial gap between updates. Once softflowd sends another update the errors should subside. You can tell softflowd to send another update immediately with the following command in an OpenWRT shell:

```softflowctl send-template```