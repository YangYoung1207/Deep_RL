#!/bin/bash
echo "Starting Data Generation"

# Remove the old data file
#mv data_sets/dset.csv data_sets/dset_OLD.csv

minGamma=-1.57
maxGamma=1.57
gamma_groups=5 

#minBeta=-1.57
#maxBeta=1.57
#beta_groups=5

speed_min=1.0 # 1.0 # 1.0 cm/s
speed_max=1.0 # 100.0 # 1 m/s
speed_groups=1

let "totalSimulations = gamma_groups * speed_groups"

echo $totalSimulations

for ((i=0; i < $gamma_groups; i++)); do
	for ((k=$speed_groups - 1; k >= 0; k--)); do

	 	# Define gamma and beta here 
	  	gamma=$(echo "((3.14/2.0 - ($i * 3.14 / (2 * $gamma_groups))))" | bc -l)
	 
	  	#beta=$(echo "((3.14/2.0 - ($j * 3.14 / (2 * $beta_groups))))" | bc -l)
	 
	  	# Default units for number are in CENTIMETERS 
	  	speed=$(echo "(($speed_min + ($k * ($speed_max - $speed_min) / $speed_groups)))" | bc -l)
	 	
		echo $speed
			
		let "currentSimulationNumber = (i * gamma_groups) + k"
                logFileName="logs/$currentSimulationNumber"
               	./myexe setup.json $gamma $speed > $logFileName
	done	
done

echo "Finished Generating Data"

