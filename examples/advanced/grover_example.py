from sympy import pprint
from sympy.physics.quantum import *
from sympy.physics.quantum.qubit import *
from sympy.physics.quantum.grover import OracleGate, WGate
from sympy.physics.quantum import grover

def demo_vgate_app(v):
    for i in range(2**v.nqubits):
        print 'apply_operators(v*IntQubit({0}, {1}))'.format(i, v.nqubits)
        pprint(apply_operators(v*IntQubit(i, v.nqubits)))

def return_true_on_one(qubits):
    return True if qubits == IntQubit(1, qubits.nqubits) else False

def main():
    print ''
    print 'Demonstration of Grover\'s Algorithm'
    print 'The OracleGate or V Gate carries the unknown function f(x)'
    print '> V|x> = ((-1)^f(x))|x> where f(x) = 1 (True in our implementation)'
    print '> when x = a, 0 (False in our implementation) otherwise'
    print ''

    nqubits = 2
    print 'nqubits = ', nqubits

    v = OracleGate(nqubits, return_true_on_one)
    print 'Oracle or v = OracleGate(%r, return_true_on_one)' % nqubits
    print ''

    psi = grover._create_computational_basis(nqubits)
    print 'psi:'
    pprint(psi)
    demo_vgate_app(v)
    print 'apply_operators(v*psi)'
    pprint(apply_operators(v*psi))
    print ''

    w = WGate(nqubits)
    print 'WGate or w = WGate(%r)' % nqubits
    print 'On a 2 Qubit system like psi, 1 iteration is enough to yield |1>'
    print 'apply_operators(w*v*psi)'
    pprint(apply_operators(w*v*psi))
    print ''

    nqubits = 3
    print 'On a 3 Qubit system, it requires 2 iterations to achieve'
    print '|1> with high enough probability'
    psi = grover._create_computational_basis(nqubits)
    print 'psi:'
    pprint(psi)
  
    v = OracleGate(nqubits, return_true_on_one)
    print 'Oracle or v = OracleGate(%r, return_true_on_one)' % nqubits
    print ''

    print 'iter1 = grover.grover_iteration(psi, v)'
    iter1 = apply_operators(grover.grover_iteration(psi, v))
    pprint(iter1)
    print '' 

    print 'iter2 = grover.grover_iteration(iter1, v)'
    iter2 = apply_operators(grover.grover_iteration(iter1, v))
    pprint(iter2)
    print '' 

main()
