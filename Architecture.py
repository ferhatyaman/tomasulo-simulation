from Entry import *


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
                rs.vk = value
                rs.qk = ''

    def flush(self, inst_id):
        for rs in self.list:
            if rs.busy and rs.inst_id == inst_id:
                rs.busy = False
                rs.qj = ''
                rs.qk = ''


class InstructionQueue:
    def __init__(self, window_size, program):
        self.queue = []
        self.size = window_size
        for i in range(window_size):
            self.queue.append(program[i * 4].copy())
        self.curr_id = 0
        self.next_id = window_size

    def __str__(self):
        file = ''
        for inst in self.queue[0:self.size]:
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
        # if len(self.queue) < self.size:
        self.queue.append(inst)

    def flush(self):
        while not self.empty():
            self.queue.pop(0)


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
            self.tail = (self.tail + 1) % self.size

            return self.list[tmp].name

    def getby_reg(self, reg_name):
        for rob in self.list:
            if rob.busy and rob.dest == reg_name:
                return rob
        return None

    def getby_rob_id(self, rob_id):
        for rob in self.list:
            if rob.name == rob_id:
                return rob

    def get_head(self):
        return self.list[self.head]

    def update_head(self):
        self.head = (self.head + 1) % self.size

    def flush(self):
        for i, rob in enumerate(self.list):
            if rob.op.startswith('B') and rob.busy and rob.ready and rob.value == 0:
                rob_list = []
                rob.busy = False
                while i != self.head:
                    if self.list[i].busy:
                        rob_list.append(self.list[i])
                        self.list[i].busy = False
                        self.tail = (self.tail - 1) % self.size
                    i = (i + 1) % self.size
                return rob_list

    def is_empty(self):
        for rob in self.list:
            if rob.busy is True:
                return False
        return True


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
            if self.cycle > 0:
                self.execute()
            self.print_CDB()
            if self.cycle > 1:
                self.write_back()
            if self.cycle > 2:
                self.commit()
            self.update_clock()
        self.print_cycle()

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

    def print_CDB(self):
        print('\nCommon Data Bus')
        if len(self.CDB) != 0:
            print(self.CDB[0])

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
                if self.RS.is_available(next_inst.op):
                    inst_id, inst = self.IQ.dequeue()
                else:
                    return
            else:
                if self.RS.is_available(next_inst.op):
                    inst_id, inst = self.IQ.dequeue()
                else:
                    return

            rob_id = self.ROB.list[self.ROB.tail].name

            rs = self.RS.get_rs(inst.op)
            rs.busy = True
            rs.inst_id = inst_id
            rs.op = inst.op
            rs.dest = rob_id

            # Case of Branch
            # Branch Prediction
            if inst.op == 'LD':
                if Instruction.is_operand_reg(inst.s1):
                    if self.RF.is_available(inst.s1):
                        rob_s1 = self.ROB.getby_reg(inst.s1)
                        if rob_s1.ready:
                            rs.vj = rob_s1.value
                            rs.qj = ''
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
            elif inst.op == 'BGE':
                if Instruction.is_operand_reg(inst.d):
                    if not self.RF[inst.d].busy:
                        rob_d = self.ROB.getby_reg(inst.d)
                        if rob_d is not None:
                            if rob_d.ready:
                                rs.vj = rob_d.value
                                rs.qj = ''
                                self.RF[inst.d].reorder = rob_id
                                self.RF[inst.d].busy = True

                            else:
                                rs.qj = rob_d.name
                        else:
                            rs.vj = self.RF[inst.d].value
                            rs.qj = ''
                    else:
                        rob_d = self.ROB.getby_reg(inst.d)
                        if rob_d.name == self.RF[inst.d].reorder:
                            rs.qj = rob_d.name
                        else:
                            rs.vj = self.RF[inst.d].value
                            rs.qj = ''
                else:
                    rs.vj = int(inst.d)
                    rs.qj = ''

                if Instruction.is_operand_reg(inst.s1):
                    if not self.RF[inst.s1].busy:
                        rob_s1 = self.ROB.getby_reg(inst.s1)
                        if rob_s1 is not None:
                            if rob_s1.ready:
                                rs.vk = rob_s1.value
                                rs.qk = ''
                                self.RF[inst.s1].reorder = rob_id
                                self.RF[inst.s1].busy = True
                            else:
                                rs.qk = rob_s1.name
                        else:
                            rs.vk = self.RF[inst.s1].value
                            rs.qk = ''
                    else:
                        rob_s1 = self.ROB.getby_reg(inst.s1)
                        if rob_s1.name == self.RF[inst.s1].reorder:
                            rs.qk = rob_s1.name
                        else:
                            rs.vk = self.RF[inst.s1].value
                            rs.qk = ''
                else:
                    rs.vk = int(inst.s1)
                    rs.qk = ''
            else:
                if Instruction.is_operand_reg(inst.s1):
                    if not self.RF[inst.s1].busy:
                        rob_s1 = self.ROB.getby_reg(inst.s1)
                        if rob_s1 is not None:
                            if rob_s1.ready:
                                rs.vj = rob_s1.value
                                rs.qj = ''
                                self.RF[inst.s1].reorder = rob_id
                                self.RF[inst.s1].busy = True

                            else:
                                rs.qj = rob_s1.name
                        else:
                            rs.vj = self.RF[inst.s1].value
                            rs.qj = ''
                    else:
                        rob_s1 = self.ROB.getby_reg(inst.s1)
                        if rob_s1.name == self.RF[inst.s1].reorder:
                            rs.qj = rob_s1.name
                        else:
                            rs.vj = self.RF[inst.s1].value
                            rs.qj = ''
                else:
                    rs.vj = int(inst.s1)
                    rs.qj = ''

                if Instruction.is_operand_reg(inst.s2):
                    if not self.RF[inst.s2].busy:
                        rob_s2 = self.ROB.getby_reg(inst.s2)
                        if rob_s2 is not None:
                            if rob_s2.ready:
                                rs.vk = rob_s2.value
                                rs.qk = ''
                                self.RF[inst.s2].reorder = rob_id
                                self.RF[inst.s2].busy = True
                            else:
                                rs.qk = rob_s2.name
                        else:
                            rs.vk = self.RF[inst.s2].value
                            rs.qk = ''
                    else:
                        rob_s2 = self.ROB.getby_reg(inst.s2)
                        if rob_s2.name == self.RF[inst.s2].reorder:
                            rs.qk = rob_s2.name
                        else:
                            rs.vk = self.RF[inst.s2].value
                            rs.qk = ''
                else:
                    rs.vk = int(inst.s2)
                    rs.qk = ''
            # TODO branch ise roba ekleme
            self.ROB.add(inst_id, inst)
            self.RF[inst.d].reorder = rob_id

    def execute(self):
        self.RS.execute(self.CDB)

    def write_back(self):
        if len(self.CDB) != 0:
            rob_id, value = self.CDB.pop(0)

            rob = self.ROB.getby_rob_id(rob_id)
            rob.ready = True
            rob.value = value
            if rob.op.startswith('B') and rob.value == 0:
                self.cycle += 1
                self.print_cycle()
                self.flush()
                self.PC = self.last_branch_PC
            self.RS.update_with_rob(rob_id, value)

    def commit(self):
        head_rob = self.ROB.get_head()
        if head_rob.ready:
            reg = self.RF[head_rob.dest]
            reg.value = head_rob.value
            if head_rob.name == reg.reorder:
                reg.reorder = ''
            head_rob.busy = False
            self.ROB.update_head()
            if self.ROB.getby_reg(reg.name) is None:
                reg.busy = False

    def update_clock(self):
        self.cycle += 1
        try:
            inst_copy = self.program[self.PC].copy()
            self.IQ.enqueue(inst_copy)
            if inst_copy.op.startswith('B'):
                self.last_branch_PC = self.PC + 4
                self.PC = int(inst_copy.s2)
            else:
                self.PC += 4
        except:
            if self.ROB.is_empty():
                self.done = True

    def flush(self):
        rob_list = self.ROB.flush()
        if rob_list is not None:
            for rob in rob_list:
                self.RS.flush(rob.inst_id)
                if self.RF[rob.dest].reorder == rob.name:
                    self.RF[rob.dest].reorder = ''
                    # eğer bu register yenilenmiş robda varsa o rob id ile güncelle
                    reg_rob = self.ROB.getby_reg(rob.dest)
                    if reg_rob is not None:
                        self.RF[rob.dest].reorder = reg_rob.name
                    else:
                        self.RF[rob.dest].busy = False
            self.IQ.flush()
        else:
            return
