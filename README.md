# Tomasulo Algorithm with Reorder Buffer
This project implements simulation environment of Tomasulo Algorithm with Reorder Buffer.
Tomasula Algorithm is dynamic hardware algorithm for dynamic scheduling of instructions 
by leveraging of multiple execution units with efficient out of order scheduling.

This algorithm uses Register Renaming, Common Data Bus, Reservation Station for every execution unit and Reorder Buffer structure to implement. 
This way we can eliminate data hazards such as read-after-write(RAW), write-after-write(WAW),
and write-after-read(WAR).

This project contains

* ```Architecture.py```  implements actual architectures of computers
* ```Component.py``` implements required data structures for algorithm
* ```Entry.py``` data structs which are used by Components
* ```main.py``` starts the simulation

There are input files as well.

* ```Instructions.txt``` shows available instructions
* ```Program.txt``` instructions which will be executed
* ```Parameters.txt``` Instruction window and number of available registers
* ```Units.txt``` available units in the architecture

And output file of simulation is  ```Report.txt``` contains status of every structure cycle by cycle.

## Simulation 
Make sure every file under same folder and run command below
```
python3 main.py
```

### Improvements TODO
Every structure can be converted to hashtable which makes more improvement to access every entry.
Instruction set can be expanded as well.

