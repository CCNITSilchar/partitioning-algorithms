### A classical approach to solve the Hypergraph bipartitioning problem is an iterative heuristic by Fiduccia and Mattheyses. This heuristic is commonly called the FM algorithm.

#### FM algorithm is a linear time heuristic for improving network partitions. New features to K-L heuristic:

1. Aims at reducing net-cut costs, the concept of cutsize is extended to hypergraphs.
2. Only a single vertex is moved across the cut in a single move.
3. Vertices are weighted.
4. Can handle "unbalanced" partitions; a balance factor is introduced.
5. A special data structure is used to select vertices to be moved across the cut to improve running time.
6. Time complexity Big-O(P), where P is the total number of terminal
