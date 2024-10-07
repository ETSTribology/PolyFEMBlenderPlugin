import os
import zipfile
import time

def zip_plugin():
    start_time = time.time()
    zipf = zipfile.ZipFile('BlenderPluginSimulation.zip', 'w', zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk('./physics_export'):
        for file in files:
            zipf.write(os.path.join(root, file))
    zipf.close()
    print(f"Zip file created in {time.time() - start_time} seconds.")
    print(f"Size of the zip file: {os.path.getsize('BlenderPluginSimulation.zip')} bytes")

zip_plugin()