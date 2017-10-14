import numpy as np
from . Util import Cell, Net, Block
import sys
import logging


class FiducciaMattheyses:
    INITIAL_BLOCK = "A"  
    r = 0.5  

    def __init__(self):
        self.cell_array = {}
        self.net_array = {}
        self.pmax = 0  

        self.blockA = None  
        
        self.blockB = None  
        
        self.cutset = 0  
        self.snapshot = None  
        self.logger = logging.getLogger("FiducciaMattheyses")

    def take_snapshot(self):
        
        self.snapshot = self.cutset
        self.blockA.take_snapshot()
        self.blockB.take_snapshot()
        for cell in self.cell_array.values():
            cell.take_snapshot()
        for net in self.net_array.values():
            net.take_snapshot()

    def load_snapshot(self):
        
        assert self.snapshot is not None
        self.cutset = self.snapshot
        self.blockA.load_snapshot()
        self.blockB.load_snapshot()
        for cell in self.cell_array.values():
            cell.load_snapshot()
        for net in self.net_array.values():
            net.load_snapshot()

    def input_routine(self, edge_matrix: np.ndarray, selection=None):
        
        assert isinstance(edge_matrix, np.ndarray)
        if selection is None:
            Q = [i for i in range(edge_matrix.shape[0])]
        else:
            Q = selection
        net = 0
        for i in range(len(Q)):
            for j in range(i + 1, len(Q)):
                if edge_matrix[Q[i]][Q[j]] == 1:
                    self.__add_pair(Q[i], Q[j], net)
                    net += 1

        for cell in self.cell_array.values():
            if cell.pins > self.pmax:
                self.pmax = cell.pins

        self.blockA = Block("A", self.pmax, self)
        self.blockB = Block("B", self.pmax, self)

        for cell in self.cell_array.values():
            cell.block = self.blockA
            self.blockA.add_cell(cell)
        for net in self.net_array.values():
            net.blockA_ref = self.blockA
            net.blockB_ref = self.blockB
        self.compute_initial_gains()
        self.blockA.initialize()

    def __add_pair(self, i: int, j: int, net_n: int):
        
        cell_i = self.__add_cell(i)
        cell_j = self.__add_cell(j)
        net = self.__add_net(net_n)

        cell_i.add_net(net)
        cell_j.add_net(net)
        net.add_cell(cell_i)
        net.add_cell(cell_j)

    def __add_cell(self, cell: int) -> Cell:
        
        if cell not in self.cell_array:
            cell_obj = Cell(cell, FiducciaMattheyses.INITIAL_BLOCK)
            self.cell_array[cell] = cell_obj
        else:
            cell_obj = self.cell_array[cell]
        return cell_obj

    def __add_net(self, net: int) -> Net:
        
        if net not in self.net_array:
            net_obj = Net(net)
            self.net_array[net] = net_obj
        else:
            net_obj = self.net_array[net]
        return net_obj

    def get_base_cell(self) -> Cell:
        
        a = self.get_candidate_base_cell_from_block(self.blockA)
        b = self.get_candidate_base_cell_from_block(self.blockB)

        if a is None and b is None:
            return None
        elif a is None and b is not None:
            return b[0]
        elif a is not None and b is None:
            return a[0]
        else:  
            bfactor_a = a[1]
            bfactor_b = b[1]
            if bfactor_a < bfactor_b:
                return a[0]
            else:
                return b[0]

    def get_candidate_base_cell_from_block(self, block: Block):  
        
        assert isinstance(block, Block)
        candidate_cell = block.get_candidate_base_cell()
        if candidate_cell is None:
            return None
        bfactor = self.get_balance_factor(candidate_cell)
        if bfactor is None:
            return None
        else:
            return candidate_cell, bfactor

    def get_balance_factor(self, cell: Cell):
        
        if cell.block.name == "A":
            A = self.blockA.size - 1
            B = self.blockB.size + 1
        else:
            assert cell.block.name == "B"
            A = self.blockA.size + 1
            B = self.blockB.size - 1
        W = A + B
        smax = self.pmax
        r = FiducciaMattheyses.r
        if r * W - smax <= A <= r * W + smax:
            return abs(A - r * W)
        else:
            return None

    def is_partition_balanced(self) -> bool:
        
        W = self.blockA.size + self.blockB.size
        smax = 1  
        r = FiducciaMattheyses.r
        A = self.blockA.size
        return r * W - smax <= A <= r * W + smax

    def compute_initial_gains(self):
        
        for cell in self.cell_array.values():
            cell.gain = 0
            for net in cell.nets:
                if cell.block.name == "A":
                    if net.blockA == 1:
                        cell.gain += 1
                    if net.blockB == 0:
                        cell.gain -= 1
                else:
                    assert cell.block.name == "B"
                    if net.blockB == 1:
                        cell.gain += 1
                    if net.blockA == 0:
                        cell.gain -= 1
                if cell.bucket_num is not None:  
                    cell.yank()

    def initial_pass(self):
        
        assert self.blockA is not None
        assert self.blockB is not None

        assert self.blockA.size >= self.blockB.size
        while not self.is_partition_balanced():
            bcell = self.blockA.get_candidate_base_cell()
            assert bcell.block.name == "A"  
            self.blockA.move_cell(bcell)

    def perform_pass(self):
        
        best_cutset = sys.maxsize

        self.compute_initial_gains()
        self.blockA.initialize()
        self.blockB.initialize()
        bcell = self.get_base_cell()
        while bcell is not None:
            if bcell.block.name == "A":
                self.blockA.move_cell(bcell)
            else:
                assert bcell.block.name == "B"
                self.blockB.move_cell(bcell)
            if self.cutset < best_cutset:
                best_cutset = self.cutset
                self.take_snapshot()

            bcell = self.get_base_cell()
        if self.snapshot is not None:
            self.load_snapshot()

    def find_mincut(self):
        
        self.initial_pass()
        prev_cutset = sys.maxsize
        self.perform_pass()
        self.logger.debug("current iteration: %d cutset: %d" % (1, self.cutset))
        iterations = 1
        while self.cutset != prev_cutset:
            prev_cutset = self.cutset
            self.perform_pass()
            self.logger.debug("current iteration: %d cutset: %d" % (iterations + 1, self.cutset))
            iterations += 1

        self.logger.info("found mincut in %d iterations: %d" % (iterations, self.cutset))

        return [c.n for c in self.blockA.cells], [c.n for c in self.blockB.cells]
