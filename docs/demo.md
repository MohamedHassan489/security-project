# Demo Script

## Goal

Demonstrate that the Secure Communication Suite protects credentials, keys, and messages while
supporting both CLI and GUI access paths.

## Demo Steps

1. Start the server:

   ```bash
   python3 -m secure_suite server
   ```

2. Start the CLI client:

   ```bash
   python3 -m secure_suite client
   ```

3. Register and login as `alice`, then send a message to `bob`.

4. Start the GUI client:

   ```bash
   python3 -m secure_suite gui
   ```

5. Register and login as `bob`, click `Refresh`, and show the received message.

6. Show that network plaintext is not visible:

   ```bash
   sudo tcpdump -i lo0 -A 'port 9999'
   ```

7. Show that the server keystore is encrypted:

   ```bash
   hexdump -C keystore.bin | head
   ```

8. Explain that MD5/DES are excluded from the production path and only discussed as weak legacy
   algorithms in the report.
