####################################################################################
# This code is basic implementaion of the algorithm described in the paper 
# by Kazuki Ikeda, Yuma Nakamura and Travis S. Humble, 2019 , "Application
# of Quantum Annealing to Nurse Scheduling Problem". 
#
# The goal is to solve a besic instance of the well known Nurse 
# Scheduling Porblem and run on a D-Wave's QPU (Quntum Processing Unit).
# This is part of the semester project of class (MATH 303) Quantum Qomputing
# in Technical University of Crete (by Prof Dr. D. Aggelakis)
#
# Author: Thomas Lagkalis
# Date: 08/02/2023
# @Technical University of Crete
#####################################################################################

from dimod import BinaryQuadraticModel, ExactSolver
from collections import defaultdict
from dwave.system import LeapHybridSampler
from copy import deepcopy
import time, argparse

parser = argparse.ArgumentParser(description='An expirimental algorithm for the Nurse Scheduling Problem. Implemented for D-Wave\'s QPU')
parser.add_argument('nurses', metavar="N", type=int, help='The number of nurses')
parser.add_argument('days', metavar="D", type=int, help='The number of days in the schedule')
parser.add_argument("--hybrid", help="Run the algorithm on a hybrid solver (default is classical solver)",
                    action="store_true")
args = parser.parse_args()

# Define basic problem parameters
num_of_nurses = args.nurses 
num_of_days = args.days    #Days in the schedule
a = 1   #Parameter for hard nurse constraint 
lamda = 1  #Weight parameter for hard shift constraint
gamma = 1   #Weight parameter for shoft nurse constraint 
min_work_days = int(num_of_days/num_of_nurses) #Minimum duty days for all n nurses
workforce = 1   #W(d)
effort = 1      #E(n)
preference = 1  #G(n,d)

# A bijective function which maps two integers (x, y) to 
# a unique integer which will be the composite index.
# In the context of NSP matrix J uses composites indicies.
def get_composite_index(x, y):
    # Assuming x and y are non-negative integers
    return (x + y) * (x + y + 1) // 2 + y

# The inverse of get_composite_index(x,y). 
# Takes a composite index and returns the two integers (x,y)
# such that index(x,y) = index.
def inverse_composite_index(index):
    w = int((8 * index + 1)**0.5 - 1) // 2
    t = (w**2 + w) // 2
    y = index - t
    x = w - y
    return x, y

def build_BQM():
    
    keys = []
    values = []
    J = defaultdict(int)
    # Defining hard nurse constraint i.e. no nurse should work two consecutive days
    for n in range(num_of_nurses):
        for d in range(num_of_days):
            n_day = get_composite_index(n, d)
            n_nextDay = get_composite_index(n, d+1)
            keys.append((n_day, n_nextDay))
            values.append(a)
            J[n_day, n_nextDay] = a

    Q = deepcopy(J)
    
    # Defining hard shift constraint i.e. at least one nurse working each day.
    # See report attached in repo for details and proofs on this.
    # First, we add the non-diagonal terms:
    for n1 in range(num_of_nurses):
        for n2 in range(num_of_nurses):
            for d in range(num_of_days):
                i = get_composite_index(n1,d)
                j = get_composite_index(n2,d)
                if i!=j:
                    Q[i,j] += lamda*effort**2

    # Then, the diagonal elements:
    for d in range(num_of_days):
        for n in range(num_of_nurses):
            i = get_composite_index(n,d)
            Q[i,i] = lamda*(effort**2-2*effort*workforce)


    # Finally, adding the soft shift constraint.
    # First, the non diagonal elements:
    for n1 in range(num_of_nurses):
        for n2 in range(num_of_nurses):
            for d in range(num_of_days):
                i = get_composite_index(n1, d)
                j = get_composite_index(n2, d)
                if i!=j:
                    Q[i,j] += gamma*preference**2

    # Then, the diagonal elements:
    for d in range(num_of_days):
        for n in range(num_of_nurses):
            i = get_composite_index(n,d)
            Q[i,i] = gamma*(preference**2-2*preference*min_work_days)
    return Q

def print_sched(shced):
    # Print the results in terminal
    print("\nOptimal schedule calculated:")
    print("\nn/d|", end='')
    for d in range(num_of_days):
        print(f" {d+1} |", end='') 

    for i in range(num_of_nurses):
        print(f"\n {i+1} |", end='')
        for j in range(num_of_days):
            if (i,j) in sched:
                print(" X |", end='')
            else:
                print("   |", end='')
    print("\n")


print(f"\nProblem Settings:\nNumber of nurses: {num_of_nurses}")
print(f"Number of days: {num_of_days}")

start = time.time()
Q = build_BQM()
bqm = BinaryQuadraticModel.from_qubo(Q)

# A fucntion to dediced which solver to use based on the user's input argument --hybrid.
def use_sampler(hybrid):
    if (hybrid):
        print("\nSending problem to hybrid sampler...")
        sampler = LeapHybridSampler()
        results = sampler.sample(bqm, label='Nurse Scheduling')
    else:
        print("\nSolving problem in local CPU...")
        sampler = ExactSolver()
        results = sampler.sample(bqm)
    return results


results = use_sampler(args.hybrid)
end = time.time()
print(f"\nEnergy of solution: {results.first.energy}")
print(f"Number of occurrences of solution: {results.first.num_occurrences}")
print(f"Time of execution: {end-start} seconds") 

best_sample = results.first.sample 

sched = [inverse_composite_index(j) for j in range(len(best_sample)) if j in best_sample and best_sample[j] == 1]

print_sched(sched)


