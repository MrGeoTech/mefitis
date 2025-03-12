# Mefitis

The sensor data gathering and presenting software suite for NDSU's Bison Pullers. Named after the 
roman goddess of posionous gasses, this platform allows us to measure sensors all over the tractor.
We use this data to improve many aspects of the tractor, including emissions and noise.

## Database Design

Database name: `data`  
Each row represents one seconds worth of data. The columns are for each different sensor.

The current sensors are as follows:  
`Sound_Engine`, `Sound_Operator`, `Emissions_Engine`, `Emissions_Operator`, `Temp_Engine`, `Temp_Exhaust`, `RPM`

