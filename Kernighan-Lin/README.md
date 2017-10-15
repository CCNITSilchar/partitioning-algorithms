# Kernighan–Lin algorithm
#### The Kernighan–Lin algorithm is a heuristic algorithm for finding partitions of graphs. The algorithm has important applications in the layout of digital circuits and components in VLSI
  
'''Pseudcode

  function Kernighan-Lin(G(V,E)):
      determine a balanced initial partition of the nodes into sets A and B
      
      do
         compute D values for all a in A and b in B
         let gv, av, and bv be empty lists
         for (n := 1 to |V|/2)
            find a from A and b from B, such that g = D[a] + D[b] - 2*c(a, b) is maximal
            remove a and b from further consideration in this pass
           add g to gv, a to av, and b to bv
           update D values for the elements of A = A \ a and B = B \ b
        end for
        find k which maximizes g_max, the sum of gv[1],...,gv[k]
        if (g_max > 0) then
           Exchange av[1],av[2],...,av[k] with bv[1],bv[2],...,bv[k]
     until (g_max <= 0)
  return G(V,E)
'''
