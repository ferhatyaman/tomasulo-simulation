class Architecture:
    def __init__(self):
        self.PC = 0
        self.cycle = 0
        # Initialize Parameters
        param_file = open('Parameters.txt', 'r')
        self.numb_reg = int(param_file.readline().strip(':\n').split(' ')[1])
        self.inst_window_size = int(param_file.readline().strip(':\n').split(' ')[1])

        # Create Registers according to params
        self.registers = {}
        for i in range(self.numb_reg):
            self.registers['R' + str(i)] = Register('R' + str(i))

        # Load Program to memory into dictionary which has keys are the address
        self.program = {}
        file = open('Program.txt', 'r')
        file.readline()  # skip file header
        for line in file.readlines():
            tmp = line.split(':')
            address = int(tmp[0])

            inst = tmp[1].strip('\n').replace(',', '').split()
            self.program[address] = Instruction.fromlist(inst)

        # Reservation Stations list
        self.RSs = []
        file = open('Units.txt', 'r')
        file.readline()  # skip file header

        for line in file.readlines():
            line_arr = line.split()
            id = int(line[0])
            name = line_arr[1]
            cycle = int(line_arr[2])
            self.RSs.append(ReservationStation(id, name, cycle))

        # Instruction Queue
        self.inst_queue = []
        for i in range(self.inst_window_size):
            self.inst_queue.append(self.program[i*4].copy())

        # ReOrder Buffer
        self.H = 0
        self.T = 0
        self.ROB = []
        for i in range(5):
            self.ROB.append(ROBInst('ROB'+str(i)))

    def start(self):
        self.print_cycle()

    def print_cycle(self):
        print('------------------------')
        print('CYCLE', self.cycle)

        print('\nInstruction Window')
        for inst in self.inst_queue:
            print(inst)

        print('\nRegisters')
        for reg in self.registers:
            print(reg)

        print('\nReservation Stations')
        for rs in self.RSs:
            print(rs)

        print('\nReorder Buffer')
        for i, rob in enumerate(self.ROB):
            if i == self.H:
                print(str(rob) + ' - (H)')
            elif i == self.T:
                print(str(rob) + ' - (T)')
            else:
                print(rob)

class ROBInst:
    def __init__(self, name):
        self.name = name
        self.op = ''
        self.busy = False
        self.ready = True
        self.dest = ''
        self.value = 0

    def __str__(self):
        if self.op == '':
            return self.name + ': '
        else:
            return self.name + ': ' + self.op + ' ' + self.dest

class ReservationStation:
    def __init__(self, id, name, cycle):
        self.id = id
        self.unit_name = name
        self.op = ""
        self.busy = False
        self.vj = 0
        self.vk = 0
        self.qj = ""
        self.qk = ""
        self.dest = ""
        self.cycle = cycle
        self.counter = self.cycle

    def __str__(self):
        if self.op == '':
            return 'RS' + str(self.id) + ':'
        else:
            return 'RS' + str(self.id) + ': ' + self.op + ' ' + str(self.vj) + ' ' + str(self.vk) + ' ' + self.dest


class Register:
    def __init__(self,name):
        self.name = name
        self.value = 0
        self.reorder = '-'
        self.busy = False

    def __str__(self):
        return self.name + ': ' + str(self.value) + ' ' + self.reorder


class Instruction:
    def __init__(self, inst_name, d, r1 , r2 = None):
        self.inst_name = inst_name
        self.d = d
        self.r1 = r1
        self.r2 = r2

    def copy(self):
        return Instruction(self.inst_name, self.d, self.r1, self.r2)

    def __str__(self):

        if self.r2 is None:
            return self.inst_name + ' ' + self.d + ', ' + self.r1
        else:
            return self.inst_name + ' ' + self.d + ', ' + self.r1 + ', ' + self.r2

    @classmethod
    def fromlist(cls,inst_list):
        if len(inst_list) == 3:
            return cls(inst_list[0],inst_list[1], inst_list[2])
        else:
            return cls(inst_list[0],inst_list[1], inst_list[2], inst_list[3])




