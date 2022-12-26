# Makes it easier to find the app ids
import json
import subprocess

endpoint = "luna://com.palm.applicationManager/listLaunchPoints"
payload = {}
command = ["/usr/bin/luna-send", "-n", "1"]
command.append(endpoint)
command.append(json.dumps(payload))
print("running command: %s" % command)
output = subprocess.check_output(command)

output_dict = json.loads(output)

apps = output_dict['launchPoints']
print(apps)
for app in apps:
    print(app['title'] + " : " + app['id'])
