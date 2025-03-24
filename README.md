# Mefitis

The sensor data gathering and presenting software suite for NDSU's Bison Pullers. Named after the 
roman goddess of poisonous gasses, this platform allows us to measure sensors all over the tractor.
We use this data to improve many aspects of the tractor, including emissions and noise.

## Database Design

Database name: `data`  
Each row represents one seconds worth of data. The columns are for each different sensor.

The current sensors are as follows:  
`Sound_Engine`, `Sound_Operator`, `Emissions_Engine`, `Emissions_Operator`, `Temp_Engine`, `Temp_Exhaust`, `RPM`

## Arduino Uno 3

#### Installing

Pre-req: `arduino-cli`

You can either install the software from the pi or from any other computer. Start by going into the
`arduino` directory.

Next, compile and upload the code:

```bash
sudo arduino-cli compile --fqbn arduino:avr:uno arduino.ino
sudo arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:uno arduino.ino
```

Now simply plug in the arduino to the pi, start the webserver, and everything should be working.

## Raspberry Pi

#### Installation

To install of a raspberry pi, first, install Raspbian Minimal 64-bit OS onto the SD card. Make sure that the username
is `pullers`.

Next, make sure to update the system and then install `git` and `postgresql`.

```bash
sudo apt update
sudo apt upgrade
sudo apt install -y git postgresql libpg-dev
sudo apt autoremove
```

Next, configure `postgresql` by running `sudo -u postgres psql`. This should take you to a SQL shell.
To configure from there, first create a new database called `data`.

```sql
CREATE TABLE IF NOT EXISTS data (id SERIAL PRIMARY KEY, Sound_Engine REAL, Sound_Operator REAL, Emissions_Engine REAL, Emissions_Operator REAL, Temp_Engine REAL, Temp_Exhaust REAL, RPM INTEGER);
```

Then set the postgres user password.

```sql
ALTER USER postgres with encrypted password 'postgres';
```

You should now be able to exit the SQL shell. Next, setup configure git with whatever username and 
email you want. Now, you will have to install nix. To do this, simply run `sh <(curl -L https://nixos.org/nix/install) --daemon`.
You should be able to just follow the prompts and it should install nicely.

After installing nix, restart the system.

Now, download the git repo into the home folder using `git clone https://github.com/MrGeoTech/mefitis.git`.

Finally, setup a python venv at `~/venv`. Make sure to add the following python packages:
`w1thermsensor[async] pyserial psycopg2 gpiozero RPi.GPIO`

#### Running

To run the program on the pi, first go into the `pi` directory and run `nix-shell`. This should
setup the environment to run the server in. Next, just run `sh ./run.sh` and everything should start.
