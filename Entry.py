class ROBEntry:
    def __init__(self, name):
        self.name = name
        self.op = ''
        self.inst_id = -1
        self.busy = False
        self.ready = True
        self.dest = ''
        self.value = None

    def __str__(self):
        if not self.busy:
            return self.name + ': '
        else:
            if self.value is None:
                return self.name + ': ' + self.op + ' ' + self.dest
            else:
                return self.name + ': ' + self.op + ' ' + self.dest + ' ' + str(self.value)

    def update(self, op, inst_id, dest, busy, ready, value=None):
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
                    if self.counter == 0:
                        self.busy = False
                        self.counter = self.cycle
                    return [self.dest, self.vj]
            else:
                if self.qj == '' and self.qk == '':
                    if self.counter == 0:
                        self.busy = False
                        self.counter = self.cycle
                        if self.op == 'ADD':
                            return [self.dest, self.vj + self.vk]
                        if self.op == 'SUB':
                            return [self.dest, self.vj - self.vk]
                        if self.op == 'MUL':
                            return [self.dest, self.vj * self.vk]
                        if self.op == 'DIV':
                            return [self.dest, self.vj / self.vk]
                        if self.op == 'BGE':
                            return [self.dest, 1 if self.vj >= self.vk else 0]
                    else:
                        self.counter -= 1
                        return
        else:
            return

    def __str__(self):
        if not self.busy:
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
