class RegisterFile:
    def __init__(self, numb_reg):
        self.registers = {}
        for i in range(numb_reg):
            self.registers['R' + str(i)] = Register('R' + str(i))

    def __str__(self):
        file = ''
        for reg in self.registers.values():
            file += str(reg) + '\n'

        return file

    def __getitem__(self, key):
        return self.registers[key]

    def is_available(self, reg):
        return not self.registers[reg].busy


class ReservationStation:
    def __init__(self):
        self.list = []
        file = open('Units.txt', 'r')
        file.readline()  # skip file header

        for line in file.readlines():
            line_arr = line.split()
            id = int(line[0])
            name = line_arr[1]
            cycle = int(line_arr[2])
            self.list.append(RSEntry(id, name, cycle))

    def is_available(self, op):
        for rs in self.list:
            if not rs.busy and op in rs.unit_names:
                return True

    def get_rs(self, op):
        for rs in self.list:
            if not rs.busy and op in rs.unit_names:
                return rs

    def __str__(self):
        file = ''
        for rs in self.list:
            file += str(rs) + '\n'
        return file

    def execute(self, CDB):
        for rs in self.list:
            value = rs.execute()
            if value is not None:
                CDB.append(value)

    def update_with_rob(self, rob_id, value):
        for rs in self.list:
            if rs.qj == rob_id:
                rs.vj = value
                rs.qj = ''
            if rs.qk == rob_id:
                rs.vk = rob_id
                rs.qk = ''
            rs.busy = False


class InstructionQueue:
    def __init__(self, window_size, program):
        self.queue = []
        for i in range(window_size):
            self.queue.append(program[i * 4].copy())
        self.curr_id = 0
        self.next_id = window_size

    def __str__(self):
        file = ''
        for inst in self.queue:
            file += str(inst) + '\n'

        return file

    def dequeue(self):
        self.curr_id += 1
        return [self.curr_id - 1, self.queue.pop(0)]

    def get(self):
        return self.queue[0].copy()

    def empty(self):
        return len(self.queue) == 0

    def enqueue(self, inst):
        self.queue.append(inst)


class ReOrderBuffer:
    def __init__(self):
        self.head = 0
        self.tail = 0
        self.list = []
        self.size = 5
        for i in range(self.size):
            self.list.append(ROBEntry('ROB' + str(i)))

    def is_full(self):
        return self.head == self.tail and not self.list[self.head].ready

    def __str__(self):
        # TODO: Burası olmadı buraya tekrar bak
        file = ''
        for i, rob in enumerate(self.list):
            if i == self.head and i == self.tail:
                file += str(rob) + ' - (H) - (T)\n'
            elif i == self.head:
                file += str(rob) + ' - (H)\n'
            elif i == self.tail:
                file += str(rob) + ' - (T)\n'
            else:
                file += str(rob) + '\n'
        return file

    def add(self, inst_id, inst):
        if self.is_full():
            raise IndexError("ROB is full, smthg is wrong.")
        else:
            self.list[self.tail].update(inst.op, inst_id, inst.d, True, False)
            tmp = self.tail
            self.tail += 1 % self.size

            return self.list[tmp].name

    def getby_reg(self,reg_name):
        for rob in self.list:
            if rob.dest == reg_name:
                return rob
        return None

    def getby_rob_id(self, rob_id):
        for rob in self.list:
            if rob.name == rob_id:
                return rob

    def get_head(self):
        return self.list[self.head]


class Architecture:
    def __init__(self):
        self.PC = 16
        self.cycle = 0
        self.done = False
        # Initialize Parameters
        param_file = open('Parameters.txt', 'r')
        self.numb_reg = int(param_file.readline().strip(':\n').split(' ')[1])
        self.inst_window_size = int(param_file.readline().strip(':\n').split(' ')[1])

        # Create Register File according to params
        self.RF = RegisterFile(self.numb_reg)

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
        self.RS = ReservationStation()

        # Instruction Queue
        self.IQ = InstructionQueue(self.inst_window_size, self.program)

        # ReOrder Buffer
        self.ROB = ReOrderBuffer()

        # Common Data Bus
        self.CDB = []

    def start(self):
        while not self.done:
            self.print_cycle()
            self.issue()
            self.execute()
            self.write_back()
            self.commit()
            self.update_clock()
            self.update_exit_cond()

    def print_cycle(self):
        print('------------------------')
        print('CYCLE', self.cycle)

        print('\nInstruction Window')
        print(self.IQ)

        print('\nRegisters')
        print(self.RF)

        print('\nReservation Stations')
        print(self.RS)

        print('\nReorder Buffer')
        print(self.ROB)

    def issue(self):
        if self.IQ.empty():
            return

        if not self.ROB.is_full():
            next_inst = self.IQ.get()

            if next_inst.op == 'LD':
                if self.RS.is_available(next_inst.op):
                    inst_id, inst = self.IQ.dequeue()
                else:
                    return
            elif next_inst.op == 'BGE':
                # TODO: Branch Prediction Yapman lazım
                pass
            else:
                if self.RS.is_available(next_inst.op):
                    inst_id, inst = self.IQ.dequeue()
                else:
                    return

            rob_id = self.ROB.add(inst_id, inst)

            rs = self.RS.get_rs(inst.op)
            rs.busy = True
            rs.inst_id = inst_id
            rs.op = inst.op
            rs.dest = rob_id

            self.RF[inst.d].reorder = rob_id

            # Case of Branch
            # Branch Prediction
            if inst.op.startswith('B'):
                pass
            elif inst.op == 'LD':
                if Instruction.is_operand_reg(inst.s1):
                    if self.RF.is_available(inst.s1):
                        rob_s1 = self.ROB.getby_reg(inst.s1)
                        if rob_s1.ready:
                            rs.vj = rob_s1.value
                            rs.qj = ''
                            # TODO S1 da update edilmeli mi?
                            self.RF[inst.s1].reorder = rob_id
                            self.RF[inst.s1].busy = True
                        else:
                            rs.qj = rob_id
                    else:
                        rs.vj = self.RF[inst.s1].value
                        rs.qj = ''
                else:
                    rs.vj = int(inst.s1)
                    rs.qj = ''
            else:
                if Instruction.is_operand_reg(inst.s1):
                    if self.RF.is_available(inst.s1):
                        rob_s1 = self.ROB.getby_reg(inst.s1)
                        if rob_s1.ready:
                            rs.vj = rob_s1.value
                            rs.qj = ''
                            # TODO S1 da update edilmeli mi?
                            self.RF[inst.s1].reorder = rob_id
                            self.RF[inst.s1].busy = True

                        else:
                            rs.qj = rob_s1.name
                    else:
                        rs.vj = self.RF[inst.s1].value
                        rs.qj = ''
                else:
                    rs.vj = int(inst.s1)
                    rs.qj = ''

                if Instruction.is_operand_reg(inst.s2):
                    if self.RF.is_available(inst.s2):
                        rob_s2 = self.ROB.getby_reg(inst.s2)
                        if rob_s2.ready:
                            rs.vk = rob_s2.value
                            rs.qk = ''
                            # TODO S2 da update edilmeli mi?
                            self.RF[inst.s2].reorder = rob_id
                            self.RF[inst.s2].busy = True
                        else:
                            rs.qk = rob_s2.name
                    else:
                        rs.vk = self.RF[inst.s2].value
                        rs.qk = ''
                else:
                    rs.vk = int(inst.s2)
                    rs.qk = ''


    def execute(self):
        self.RS.execute(self.CDB)

    def write_back(self):
        if self.cycle != 0 and len(self.CDB) != 0:
            rob_id, value = self.CDB.pop(0)

            rob = self.ROB.getby_rob_id(rob_id)
            rob.ready = True
            rob.value = value

            self.RS.update_with_rob(rob_id, value)

    def commit(self):
        head_rob = self.ROB.get_head()
        if head_rob.ready:
            reg = self.RF[head_rob.dest]
            reg.value = head_rob.value
            head_rob.busy = False
            if self.ROB.getby_reg(reg.name) is None:
                reg.busy = False

    def update_clock(self):
        self.cycle += 1
        self.IQ.enqueue(self.program[self.PC].copy())
        self.PC += 4

    def update_exit_cond(self):
        try:
            inst = self.program[self.PC]
        except:
            self.done = True



class ROBEntry:
    def __init__(self, name):
        self.name = name
        self.op = ''
        self.inst_id = -1
        self.busy = False
        self.ready = True
        self.dest = ''
        self.value = 0

    def __str__(self):
        if self.op == '':
            return self.name + ': '
        else:
            return self.name + ': ' + self.op + ' ' + self.dest

    def update(self, op, inst_id, dest, busy, ready, value=0):
        self.op = op
        self.inst_id = inst_id
        self.dest = dest
        self.value = value
        self.busy = busy
        self.ready = ready


class RSEntry:
    def __init__(self, id, name, cycle):
        self.id = id
        self.inst_id = -1
        self.op = ""
        self.busy = False
        self.vj = 0
        self.vk = 0
        self.qj = ""
        self.qk = ""
        self.dest = ""

        # Functional Unit Params
        self.unit_names = name.split(',')
        self.cycle = cycle
        self.counter = self.cycle

    def execute(self):
        if self.busy:
            # TODO: BRANCH PREDICTION
            if self.op == 'LD':
                if self.qj == '':
                    self.counter -= 1
                    return [self.dest, self.vj]
            else:
                if self.counter == 0 and (self.qj != '' or self.qk != ''):
                    self.counter -= 1
                    if self.op == 'ADD':
                        return [self.dest, self.vj + self.vk]
                    if self.op == 'SUB':
                        return [self.dest, self.vj - self.vk]
                    if self.op == 'MUL':
                        return [self.dest, self.vj * self.vk]
                    if self.op == 'DIV':
                        return [self.dest, self.vj / self.vk]

        else:
            return

    def __str__(self):
        if self.op == '':
            return 'RS' + str(self.id) + ':'
        else:
            line = 'RS' + str(self.id) + ': ' + self.op + ' '
            if self.qj != '':
                line += self.qj + ' '
            else:
                line += str(self.vj) + ' '
            if self.qk != '':
                line += self.qk + ' '
            else:
                line += str(self.vk) + ' '
            return line + self.dest


class Register:
    def __init__(self, name):
        self.name = name
        self.value = None
        self.reorder = None
        self.busy = False

    def __str__(self):
        if self.value is None and self.reorder is None:
            return self.name + ': '
        elif self.value is None:
            return self.name + ': ' + '\t' + ' ' + self.reorder
        elif self.reorder is None:
            return self.name + ': ' + str(self.value)
        else:
            return self.name + ': ' + str(self.value) + ' ' + self.reorder

    def update(self, rob, value, busy):
        self.value = value
        self.reorder = rob
        self.busy = busy


class Instruction:
    def __init__(self, op_name, d, s1, s2=None):
        self.op = op_name
        self.d = d
        self.s1 = s1
        self.s2 = s2

    def copy(self):
        return Instruction(self.op, self.d, self.s1, self.s2)

    @staticmethod
    def is_operand_reg(operand):
        try:
            value = int(operand)
            return False
        except:
            return True

    def __str__(self):

        if self.s2 is None:
            return self.op + ' ' + self.d + ', ' + self.s1
        else:
            return self.op + ' ' + self.d + ', ' + self.s1 + ', ' + self.s2

    @classmethod
    def fromlist(cls, inst_list):
        if len(inst_list) == 3:
            return cls(inst_list[0], inst_list[1], inst_list[2])
        else:
            return cls(inst_list[0], inst_list[1], inst_list[2], inst_list[3])
