from z3 import Bool, BoolVal, Solver, And, Sum, Implies, Or
import csv

gridFile = "demogrid.csv"
X = 11

# numbers of meaningful spots
# other numbers just indicate when types match, nothing else
startSpot = "0"
goalSpot = "1"
deathSpot = "2"
iceSpot = "3"

typeTotal = 8

solverOverall = Solver()


def read_grid(filename):
  with open(filename, 'r') as file:
    # Return a reader object which will
    # iterate over lines in the given csvfile
    grid_reader = csv.reader(file)
    
    # convert string to list
    grid = list(grid_reader)
    return grid

grid = read_grid(gridFile) 


startLocations = []
for row in range(len(grid)):
	for column in range(len(grid[row])):
		if grid[row][column] == startSpot:
			startLocations.append((row, column))

# TEMPORARY
startLocations = [startLocations[0]]
print(startLocations)

solverList = [Solver() for x in range(len(startLocations))]


for start in range(len(startLocations)):
	print(startLocations[start])
	# this will neeed to be in a loop over all start locations
	# now make a matrix the shape of the grid
	robotLocationBegin = [ [ BoolVal((x,y) == startLocations[start]) for y in range(len(grid[x]))] for x in range(len(grid))]

	robotMovements = [ [ [ Bool(f"square{x},{y}_turn{t}") for y in range(len(grid[x]))] for x in range(len(grid))] for t in range(X)]

	robotMovements = [robotLocationBegin] + robotMovements


	# the movement rules per tile type
	# directions will be 1 north 2 east 3 south 4 west
	movementTypes = [ [Bool(f"type{t}_direction{d}") for d in range(4)] for t in range(typeTotal)]

	# only 1 allowable direction per type
	solverList[start].add(And([Sum(x) == 1 for x in movementTypes]))


	# movement rules

	# the player will only be in one location per turn
	for turn in robotMovements:
		solverList[start].add(Sum([Sum(row) for row in turn]) == 1)

	# the movement will be in the cardinal directions
	for t in range(1, len(robotMovements)):
		for row in range(len(robotMovements[t])):
			for column in range(len(robotMovements[row])):
				# calculate the valid moves based on the cardinal directions
				# ignoring going over the edge attempts as only maximum moves to reach goal, not minimum
				# similarly ignoring the lava squares
				cardinalSurrondings = []
				if row != 0 and grid[row - 1][column] != deathSpot:
					cardinalSurrondings.append((row - 1, column))
				if row != len(grid) - 1 and grid[row + 1][column] != deathSpot:
					cardinalSurrondings.append((row + 1, column))
				if column != 0 and grid[row][column - 1] != deathSpot:
					cardinalSurrondings.append((row, column - 1))
				if column != len(grid[0]) - 1 and grid[row][column + 1] != deathSpot:
					cardinalSurrondings.append((row, column + 1))


				# if the player was in a location last turn, it must be within the cardinal directions the next
				solverList[start].add(Implies(robotMovements[t - 1][row][column], Or([robotMovements[t][coord[0]][coord[1]] for coord in cardinalSurrondings])))

				# the player must also obey the decided movement direction based on tile type
				# solverList[start].add(Implies(robotMovements[t - 1][row][column], ))




	# for each of these paths, a goal state will be reached
	goalLocations = []
	for row in range(len(grid)):
		for column in range(len(grid[row])):
			if grid[row][column] == goalSpot:
				goalLocations.append((row, column))

	solverList[start].add(Or([ Or([turn[x[0]][x[1]] for x in goalLocations]) for turn in robotMovements]))




	print("-------")
	print("On start location " + str(start))
	print(solverList[start].check())
	m = solverList[start].model()


	print("Start: " + str(startLocations[0]))
	goalReached = False
	for t in range(1, len(robotMovements)):
		if not goalReached:
			for row in range(len(robotMovements[t])):
				for column in range(len(robotMovements[t][row])):
					if m[robotMovements[t][row][column]]:
						print("Turn " + str(t))
						print(row, column)

						if (row, column) in goalLocations:
							goalReached = True

