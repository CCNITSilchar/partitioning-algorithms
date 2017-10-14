import copy


class Cell:
    def __init__(self, n: int, block):
        assert n >= 0
        self.n = n  
        self.pins = 0  
        self.nets = set()  
        self.gain = 0  
        self.block = block  
        
        self.locked = False  
        self.bucket_num = None  
        
        self.snapshot = None  

    def bucket(self):
        if self.block is None:
            return None
        return self.block.bucket_array.array[self.bucket_num]

    def take_snapshot(self):
        
        self.snapshot = self.gain, self.block, self.locked, self.bucket_num

    def load_snapshot(self):
        
        assert self.snapshot is not None
        self.gain = self.snapshot[0]
        self.block = self.snapshot[1]
        self.locked = self.snapshot[2]
        self.bucket_num = self.snapshot[3]

    def add_net(self, net):
        if net not in self.nets:
            self.nets.add(net)
            self.pins += 1

    def adjust_net_distribution(self):
        
        for net in self.nets:
            if self.block.name == "A":  
                net.cell_to_blockA(self)
            else:
                assert self.block.name == "B"  
                net.cell_to_blockB(self)

    def lock(self):
        if self.locked is True:
            return
        self.locked = True
        for net in self.nets:
            if self.block.name == "A":
                net.blockA_locked += 1
                net.blockA_free -= 1
            else:
                assert self.block.name == "B"
                net.blockB_locked += 1
                net.blockB_free -= 1

    def unlock(self):
        if self.locked is False:
            return
        self.locked = False
        for net in self.nets:
            if self.block.name == "A":
                net.blockA_locked -= 1
                net.blockA_free += 1
            else:
                assert self.block.name == "B"
                net.blockB_locked -= 1
                net.blockB_free += 1

    def yank(self):
        
        self.block.bucket_array.yank_cell(self)


class Net:
    def __init__(self, n: int):
        assert n >= 0
        self.n = n  
        self.cells = set()  
        self.blockA_ref = None  
        
        self.blockB_ref = None  
        
        self.blockA = 0  
        self.blockB = 0  
        self.blockA_locked = 0  
        self.blockB_locked = 0  
        self.blockA_free = 0  
        self.blockB_free = 0  
        self.blockA_cells = []  
        self.blockB_cells = []  
        self.cut = False  
        self.snapshot = None  

    def take_snapshot(self):
        
        self.snapshot = self.blockA, self.blockB, self.blockA_locked, self.blockB_locked, self.blockA_free, \
                        self.blockB_free, copy.copy(self.blockA_cells), copy.copy(self.blockB_cells), self.cut

    def load_snapshot(self):
        
        assert self.snapshot is not None
        self.blockA = self.snapshot[0]
        self.blockB = self.snapshot[1]
        self.blockA_locked = self.snapshot[2]
        self.blockB_locked = self.snapshot[3]
        self.blockA_free = self.snapshot[4]
        self.blockB_free = self.snapshot[5]
        self.blockA_cells = self.snapshot[6]
        self.blockB_cells = self.snapshot[7]
        self.cut = self.snapshot[8]

    def add_cell(self, cell):
        
        if cell not in self.cells:
            self.cells.add(cell)
            if cell.block == "A":
                self.blockA += 1
                self.blockA_free += 1
                self.blockA_cells.append(cell)
            else:
                assert cell.block == "B"
                self.blockB += 1
                self.blockB_free += 1
                self.blockB_cells.append(cell)

    def __update_cut_state(self):
        new_cutstate = self.blockA != 0 and self.blockB != 0
        if self.cut != new_cutstate:
            if new_cutstate is True:
                self.blockA_ref.fm.cutset += 1
            else:
                self.blockA_ref.fm.cutset -= 1
            self.cut = new_cutstate

    def cell_to_blockA(self, cell):
        
        self.blockA += 1
        self.blockB -= 1
        if cell.locked is True:
            self.blockA_locked += 1
            self.blockB_locked -= 1
        else:
            self.blockA_free += 1
            self.blockB_free -= 1

        self.blockB_cells.remove(cell)
        self.blockA_cells.append(cell)
        self.__update_cut_state()
        assert self.blockA >= 0
        assert self.blockA_free >= 0
        assert self.blockB >= 0
        assert self.blockB_free >= 0
        assert self.blockA_free + self.blockA_locked == self.blockA
        assert self.blockB_free + self.blockB_locked == self.blockB

    def cell_to_blockB(self, cell):
        
        self.blockB += 1
        self.blockA -= 1
        if cell.locked is True:
            self.blockB_locked += 1
            self.blockA_locked -= 1
        else:
            self.blockB_free += 1
            self.blockA_free -= 1
        self.blockA_cells.remove(cell)
        self.blockB_cells.append(cell)
        self.__update_cut_state()
        assert self.blockA >= 0
        assert self.blockA_free >= 0
        assert self.blockB >= 0
        assert self.blockB_free >= 0
        assert self.blockA_free + self.blockA_locked == self.blockA
        assert self.blockB_free + self.blockB_locked == self.blockB

    def inc_gains_of_free_cells(self):
        
        for cell in self.cells:
            if not cell.locked:
                cell.gain += 1
                cell.yank()

    def dec_gain_Tcell(self, to_side: str):
        
        assert self.blockA_ref is not None
        assert self.blockB_ref is not None

        if to_side == "A":
            assert self.blockA_free == 1
            assert len(self.blockA_cells) == 1
            cell = self.blockA_cells[0]
            cell.gain -= 1
            cell.yank()
        else:
            assert to_side == "B"
            assert self.blockB_free == 1
            assert len(self.blockB_cells) == 1
            cell = self.blockB_cells[0]
            cell.gain -= 1
            cell.yank()

    def dec_gains_of_free_cells(self):
        
        for cell in self.cells:
            if not cell.locked:
                cell.gain -= 1
                cell.yank()

    def inc_gain_Fcell(self, from_side: str):
        
        assert self.blockA_ref is not None
        assert self.blockB_ref is not None

        if from_side == "A":
            assert self.blockA_free == 1
            assert len(self.blockA_cells) == 1
            cell = self.blockA_ref.cells[0]
            cell.gain += 1
            cell.yank()
        else:
            assert from_side == "B"
            assert self.blockB_free == 1
            assert len(self.blockB_cells) == 1
            cell = self.blockB_ref.cells[0]
            cell.gain += 1
            cell.yank()


class Block:
    def __init__(self, name: str, pmax: int, fm):
        self.name = name
        self.size = 0
        self.bucket_array = BucketArray(pmax)
        self.cells = []  
        
        self.fm = fm  
        
        self.snapshot = None  

    def take_snapshot(self):
        
        self.snapshot = self.name, self.size, copy.copy(self.cells)
        self.bucket_array.take_snapshot()

    def load_snapshot(self):
        
        assert self.snapshot is not None
        self.name = self.snapshot[0]
        self.size = self.snapshot[1]
        self.cells = self.snapshot[2]
        self.bucket_array.load_snapshot()

    def get_candidate_base_cell(self) -> Cell:
        
        return self.bucket_array.get_candidate_base_cell()

    def add_cell(self, cell: Cell):
        
        assert isinstance(cell, Cell)
        self.bucket_array.add_to_free_cell_list(cell)
        self.cells.append(cell)
        cell.block = self
        self.size += 1

    def remove_cell(self, cell: Cell):
        
        assert isinstance(cell, Cell)
        self.size -= 1
        assert self.size >= 0
        self.cells.remove(cell)
        self.bucket_array.remove_cell(cell)

    def move_cell(self, cell: Cell):
        
        assert isinstance(cell, Cell)
        comp_block = cell.block.fm.blockA if cell.block.name == "B" else cell.block.fm.blockB
        
        cell.lock()
        
        self.__adjust_gains_before_move(cell)
        
        self.remove_cell(cell)
        
        comp_block.add_cell(cell)
        
        cell.adjust_net_distribution()
        
        self.__adjust_gains_after_move(cell)

    def __adjust_gains_before_move(self, cell: Cell):
        assert isinstance(cell, Cell)
        for net in cell.nets:
            if cell.block.name == "A":
                LT = net.blockB_locked
                FT = net.blockB_free
            else:
                assert cell.block.name == "B"
                LT = net.blockA_locked
                FT = net.blockA_free
            if LT == 0:
                if FT == 0:
                    net.inc_gains_of_free_cells()
                elif FT == 1:
                    net.dec_gain_Tcell("A" if cell.block.name == "B" else "B")

    def __adjust_gains_after_move(self, cell: Cell):
        assert isinstance(cell, Cell)
        for net in cell.nets:
            if cell.block.name == "A":
                LF = net.blockB_locked
                FF = net.blockB_free
            else:
                assert cell.block.name == "B"
                LF = net.blockA_locked
                FF = net.blockA_free
            if LF == 0:
                if FF == 0:
                    net.dec_gains_of_free_cells()
                elif FF == 1:
                    net.inc_gain_Fcell("A" if cell.block.name == "B" else "B")

    def initialize(self):
        
        self.bucket_array.initialize()


class BucketArray:
    def __init__(self, pmax):
        self.max_gain = -pmax
        self.pmax = pmax
        self.array = [[] for x in range(pmax * 2 + 1)]
        self.free_cell_list = []
        self.snapshot = None  

    def take_snapshot(self):
        
        self.snapshot = self.max_gain, self.__dup_array(), copy.copy(self.free_cell_list)

    def __dup_array(self):
        clone = []
        for i in self.array:
            clone.append(copy.copy(i))
        return clone

    def load_snapshot(self):
        
        assert self.snapshot is not None
        self.max_gain = self.snapshot[0]
        self.array = self.snapshot[1]
        self.free_cell_list = self.snapshot[2]

    def __getitem__(self, i: int) -> list:
        assert -self.pmax <= i <= self.pmax
        i += self.pmax
        return self.array[i]

    def remove_cell(self, cell: Cell):
        
        assert isinstance(cell, Cell)
        cell.bucket().remove(cell)
        if self[self.max_gain] == cell.bucket() and len(cell.bucket()) == 0:
            self.decrement_max_gain()
        cell.bucket_num = None

    def yank_cell(self, cell: Cell):
        
        assert isinstance(cell, Cell)
        assert cell.locked is False

        assert -self.pmax <= cell.gain <= self.pmax
        self.remove_cell(cell)
        self.add_cell(cell)

    def decrement_max_gain(self):
        
        while self.max_gain > -self.pmax:
            self.max_gain -= 1
            if len(self[self.max_gain]) != 0:
                break

    def add_cell(self, cell: Cell):
        
        assert isinstance(cell, Cell)
        assert -self.pmax <= cell.gain <= self.pmax

        self[cell.gain].append(cell)
        cell.bucket_num = cell.gain + self.pmax
        if cell.gain > self.max_gain:
            self.max_gain = cell.gain

    def add_to_free_cell_list(self, cell: Cell):
        
        assert isinstance(cell, Cell)
        self.free_cell_list.append(cell)

    def get_candidate_base_cell(self):
        
        l = self[self.max_gain]
        if len(l) == 0:
            return None
        else:
            return l[0]

    def initialize(self):
        
        for cell in self.free_cell_list:
            cell.unlock()
            self.add_cell(cell)
        self.free_cell_list.clear()
