# PURPOSE - This program uses the quadratic formula to calculate the solutions to to a quadratic equation

import math

def quadratic_formula(a, b, c):
    solutions = []
    solution_1 = (-b - math.sqrt(abs((b**2) - (4*a*c))))/(2*a)
    solution_2 = (-b + math.sqrt(abs((b**2) - (4*a*c))))/(2*a)
    solutions.append(solution_1)
    solutions.append(solution_2)
    return(solutions)


