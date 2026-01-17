import sys
import queue
import copy
from crossword.crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        _, _, w, h = draw.textbbox((0, 0), letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
         constraints; in this case, the length of the word.)
        """
        # Iterate through each variable. Then, iterate through each word in each var domain.
        for var in self.domains:
            for word in set(self.domains[var]):
                if len(word) != var.length:
                    self.domains[var].remove(word)

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        revised = False
        # Overlaps is a dictionary that maps (v1,v2) to (i,j)
        overlap = self.crossword.overlaps[x,y]

        # If there is no overlap, there are no arc constraints
        if overlap is None:
            return False
        
        i,j = overlap
        # Choose one word on domain. If that word has a conflict (no possible y exists), remove that word
        for x_word in set(self.domains[x]):
            intersection_letter = x_word[i]
            conflict = True
            for y_word in self.domains.get(y):
                if intersection_letter == y_word[j]: # If there exists a word that could be placed there, no conflict
                    conflict = False
                    break
            if conflict:
                self.domains.get(x).remove(x_word)
                revised = True
        return revised
            
    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """
        queue_arcs = queue.Queue()
        if arcs is None:
            for x in self.domains:
                for y in self.crossword.neighbors(x):
                    queue_arcs.put((x, y))
        else:
            for arc in arcs:
                queue_arcs.put(arc)
        
        while not queue_arcs.empty():
            # Revise arc
            x, y = queue_arcs.get()
            if self.revise(x,y):
                # If there exists no more possible x's, puzzle is impossible
                if len(self.domains[x]) == 0:
                    return False
                # If domain updated, update all neighbors
                for neighbor in self.crossword.neighbors(x):
                    if neighbor != y: # We already made x arc consistent with y, no need to add it again. *logic a bit more indepth
                        queue_arcs.put((neighbor, x))
        return True


    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """
        return set(assignment.keys()) == self.crossword.variables

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """

        seen = set()
        for var in assignment.keys():
            # Ensure distinct values
            if assignment[var] in seen:
                return False
            seen.add(assignment[var])

            # Check length
            if var.length != len(assignment[var]):
                return False
            
            # Iterate through each neighbor to check if overlap is consistent
            for neighbor in self.crossword.neighbors(var):

                # If neighbor variable is filled out, check
                if neighbor in assignment.keys():
                    i,j = self.crossword.overlaps[var, neighbor]

                    # If the overlapping variable not equal
                    if assignment[var][i] != assignment[neighbor][j]:
                        return False
        return True


    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        domain = self.domains[var]
        counts = {}
        for word in domain:
            num_restricted = 0
            for neighbor in self.crossword.neighbors(var):
                # If neighbor is accounted for, continue
                if neighbor in assignment:
                    continue
                
                # Check if word in neighbor domain. If so, remove from neighbor domain. 
                # Also check if word ruins the possibility of others (through overlap + inconsistency)
                neighbor_domain = self.domains[neighbor]

                i,j = self.crossword.overlaps[var, neighbor]
                for neighbor_word in neighbor_domain:
                    if word[i] != neighbor_word[j]:
                        num_restricted += 1
            counts[word] = num_restricted
        
        # Automatically sorts based on values, and returns list of keys
        sorted_domain = sorted(counts, key=lambda w: counts[w])
        return sorted_domain

    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """
        min_domain = sys.maxsize
        for var in self.domains.keys():
            if var in assignment.keys():
                continue

            if min_domain > len(self.domains[var]):
                min_domain_var, min_domain = var, len(self.domains[var])
            elif min_domain == len(self.domains[var]):
                # min domain should be highest degree.
                if len(self.crossword.neighbors(min_domain_var)) < len(self.crossword.neighbors(var)):
                    min_domain_var = var
        
        return min_domain_var
    
        
            

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        # Return solution
        if self.assignment_complete(assignment):
            return assignment

        var_to_change = self.select_unassigned_variable(assignment)
        for word in self.order_domain_values(var_to_change, assignment):
            assignment[var_to_change] = word
            
            # If consistent, dig one more layer
            if self.consistent(assignment):
                save_domain = copy.deepcopy(self.domains) # Make a copy to undo if fails
                arcs = set()
                for neighbors in self.crossword.neighbors(var_to_change):
                    arcs.add((neighbors, var_to_change))
                if self.ac3(arcs): # If it looks plausible, continue digging
                    final_assignment = self.backtrack(assignment)
                    if final_assignment != None: #If we didn't reach dead end, return final assignment
                        return final_assignment
                self.domains = save_domain # Undo changes if ac3 failed or backtracking failed
            assignment.pop(var_to_change)
        return None


def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
