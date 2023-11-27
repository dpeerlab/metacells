import tracemalloc
import time
import scanpy as sc
import pandas as pd

import cupy as cp
import cupyx
import numpy as np
from tqdm import tqdm

import sys

# from icecream import ic

# from importlib import reload
from SEACells.core import SEACells
# reload(SEACells)

# num_cells = 10000
# ad = ad[:num_cells]

def get_data(ad, num_cells, use_gpu, use_sparse): 
  ## User defined parameters

  ## Core parameters 
  # number of SEACells
  n_SEACells = num_cells // 75
  build_kernel_on = 'X_pca' # key in ad.obsm to use for computing metacells
                            # This would be replaced by 'X_svd' for ATAC data

  ## Additional parameters
  n_waypoint_eigs = 10 # Number of eigenvalues to consider when initializing metacells

  model = SEACells(ad, 
                                 use_gpu=use_gpu, 
                                 use_sparse=use_sparse, 
                                 build_kernel_on=build_kernel_on, 
                                 n_SEACells=n_SEACells, 
                                 n_waypoint_eigs=n_waypoint_eigs,
                                 convergence_epsilon = 1e-5)
  model.construct_kernel_matrix()
  model.initialize_archetypes()

  start = time.time()
  tracemalloc.start()

  model.fit(min_iter=10, max_iter=150)

  end = time.time()
  tot_time = end - start

  mem = tracemalloc.get_traced_memory()
  tracemalloc.stop()

  assignments = model.get_hard_assignments()
  
  return assignments, tot_time, mem

def gpu_versions(ad, num_cells):
    assignments3, time3, mem3 = get_data(ad, num_cells = num_cells, use_gpu=True, use_sparse=False)
    assignments4, time4, mem4 = get_data(ad, num_cells = num_cells, use_gpu=True, use_sparse=True)

    # Write the assignments
    assignments = [assignments3, assignments4] 
    
    # Write the time and memory data
    comparisons = pd.DataFrame({'version': ['v3: yes GPU, no sparse', 'v4: yes GPU, yes sparse'], 
                           'time (s)': [time3, time4],
                           'peak memory': [mem3[1], mem4[1]]})
    
    return assignments, comparisons

def get_results(num_cell):
#    potential_num_cells = [5000, 10000, 50000, 100000, 150000, 200000]
#    for num_cell in potential_num_cells: 
        ad = sc.read("/home/aparna/DATA/aparnakumar/150000_cells/mouse_marioni_150k.h5ad") 
        ad = ad[:num_cell]
        for trial in range(5): 
            assignments, comparisons = gpu_versions(ad, num_cell)
            comparisons.to_csv(f"results/{num_cell}_cells/comparisons_{trial}.csv")

            for i in range(len(assignments)):
                if i == 0: 
                    assignments[i].to_csv(f"results/{num_cell}_cells/assignments_v3_{trial}.csv") 
                elif i == 1: 
                    assignments[i].to_csv(f"results/{num_cell}_cells/assignments_v4_{trial}.csv")

    
            print(f"Done with {num_cell} cells, trial {trial + 1}")

# Create main function 
if __name__ == "__main__": 
    # Runs get_data based on the num_cells given as command line input 
    num_cells = int(sys.argv[1])
    # print(type(num_cells))
    get_results(num_cells)
