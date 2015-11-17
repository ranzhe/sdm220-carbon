# sdm220-carbon systemd HOWTO

0. Edit ExecStart parameter in sdm220-carbon.service according to your script path
0. Copy sdm220-carbon.service to /lib/systemd/system/
0. Invoke: sudo systemctl daemon-reload
0. Enable service: sudo systemctl enable sdm220-carbon.service
0. Start service: sudo systemctl start sdm220-carbon