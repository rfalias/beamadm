# This was made in a night, it's messy and not for real use

# Bunch of random imports

import systemd.daemon
import os
import shutil
from flask import Flask, redirect, url_for, request, render_template
app = Flask(__name__)
import subprocess
from datetime import datetime
import toml
CONFIG_PATH = "/root/linux/ServerConfig.toml"
import time
MOD_PATH = '/root/linux/Resources/Client/'

# Get mod files in the mods dir
def GetMods():
  return (file for file in os.listdir(MOD_PATH))

# Restart beamng systemd service
def RestartServer():
  subprocess.run(["systemctl","restart","beamng"])

# Get server settings toml file
def GetServerSettings():
  # Read a TOML file
  with open(CONFIG_PATH, "r") as f:
    config = toml.load(f)
  return config

# Get list of maps available from maplist.toml
def GetMapList():
  with open("maplist.toml", "r") as f:
    maplist = toml.load(f)
  return maplist['maps']

# Find the selected current map from toml
def MapListToSelectBox():
  settings = GetServerSettings()
  currmap = settings['General']['Map'].split('/')[2]
  print("Current map is " + currmap)
  return currmap

# Write a new map to the toml
def ChangeMapToml(newmap):
  print(f"Changing to {newmap}")
  oldsettings = GetServerSettings()
  newmapfull = GetMapList()[newmap]
  oldsettings['General']['Map'] = newmapfull
  date_time = datetime.now().strftime("%m_%d_%y_%H%M%S")
  shutil.copyfile(CONFIG_PATH, f"{CONFIG_PATH}.{date_time}")

  with open(CONFIG_PATH, "w") as f:
    f.write(toml.dumps(oldsettings))
  time.sleep(1)
  RestartServer()
  return newmapfull
   
# Get the status of the beamng systemd unit
def GetServerStatus():
  from pystemd.systemd1 import Unit
  unit = Unit(b'beamng.service')
  unit.load()
  state = f"""Service: {unit.Unit.ActiveState.decode()} \n
  Substate: {unit.Unit.SubState.decode()}
"""
  return(state)

# Read the beamng.service jorunal file
def ReadJournal():
  import systemd.journal
  
  # Set the unit to filter the journal by
  unit = 'beamng.service'
  
  # Set the number of lines to read from the end of the journal
  lines = 10
  
  # Open the journal and set the cursor to the end
  journal = systemd.journal.Reader()
  journal.seek_tail()
  
  # Set the unit filter
  journal.add_match(_SYSTEMD_UNIT=unit)
  
  # Read the last `lines` lines of the journal
  journal.get_previous(lines)
  data = ""  
  # Iterate over the journal entries
  for entry in journal:
      datah = ""
      # Print the timestamp, message, and fields for each entry
      datah += " ".join(" [".join(entry['MESSAGE'].split('[')[3:]).split()[2:]) + '\n'
      print(f"DATAH IS ----- {datah} len= {len(datah)}")
      if len(datah) <= 1:
          continue
      else:
          data += "["
          data += datah
  return data
  
# Root page, render templates/index.html
@app.route("/" ,methods=['GET'])
def admin():
    return render_template('index.html', options=GetMapList(), state=GetServerStatus(), logs=ReadJournal(), selected=MapListToSelectBox(), mods=GetMods())

# Post only, change the map
@app.route("/changemap", methods=['POST'])
def changemap():
  ChangeMapToml(request.form.get('maps'))
  return redirect('/')

# Upload a mod
@app.route('/upload', methods=['POST'])
def upload():
  file = request.files['file']
  if file.filename == '':
    # No file was selected
    return 'No file selected'
  if file and file.filename.endswith('.zip'):
    # Save the file to the specified directory
    file.save('/root/linux/Resources/Client/{}'.format(file.filename))
    RestartServer()
    return redirect('/')
  else:
    return 'Invalid file type'

# Delete a mod
def DeleteMod(name):
  os.remove(os.path.join(MOD_PATH,name))

# Delete a mod route
@app.route('/deletemod', methods=['POST'])
def deletemod():
  for mod in request.form.getlist('mods'):
    DeleteMod(mod)
  return redirect('/')

# Main entry
if __name__ == "__main__":
    app.run(host='0.0.0.0')
