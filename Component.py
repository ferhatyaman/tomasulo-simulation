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
                rob.busy = True
                i = (i + 1) % self.size
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

