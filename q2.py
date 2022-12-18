from z3 import Bool, BoolVal, Solver, And, Sum, Implies, Or, Not
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

myGrid = read_grid(gridFile) 


startLocations = []
for row in range(len(myGrid)):
	for column in range(len(myGrid[row])):
		if myGrid[row][column] == startSpot:
			startLocations.append((row, column))

# TEMPORARY
# startLocations = [startLocations[1]]

# the list of goal states that can be reached
goalLocations = []
for row in range(len(myGrid)):
	for column in range(len(myGrid[row])):
		if myGrid[row][column] == goalSpot:
			goalLocations.append((row, column))


def findPath(startLoc, mTypes, goalList, grid, solver, robotMovements):
	robotLocationBegin = [ [ BoolVal((x,y) == startLoc) for y in range(len(grid[x]))] for x in range(len(grid))]
	robotMovements = [robotLocationBegin] + robotMovements

	# movement rules
	# the player will only be in one location per turn
	for turn in robotMovements:
		solver.add(Sum([Sum(row) for row in turn]) == 1)

	# for each spot in time, the movement will be guided by the
	# tile type
	# avoiding death tiles
	# avoiding edges
	for t in range(0, len(robotMovements) - 1):
		for row in range(len(robotMovements[t])):
			for column in range(len(robotMovements[row])):

				# the tile type at a particular location
				typeNum = int(grid[row][column])

				# get valid movement options
				# so no moving off the edge (since trying will mean eternally attempting to head off edge and thus never reaching goal)
				# no moving onto the death spots
				cardinalSurrondings = [(), (), (), ()]
				if row != 0 and grid[row - 1][column] != deathSpot:
					cardinalSurrondings[0] = (row - 1, column)

				if row != len(grid) - 1 and grid[row + 1][column] != deathSpot:
					cardinalSurrondings[2] = (row + 1, column)

				if column != 0 and grid[row][column - 1] != deathSpot:
					cardinalSurrondings[3] = (row, column - 1)

				if column != len(grid[0]) - 1 and grid[row][column + 1] != deathSpot:
					cardinalSurrondings[1] = (row, column + 1)


				# # if it is ice, add the rule constrictions to the path if you slip
				# # then continue on with these
				# if typeNum == int(iceSpot):
				# 	# calculate surrondings for ice slip
				# 	# bumping into the wall is safe, will just force it to be a single step
				# 	# but since already explore that path, will rule it out here
				# 	slipCardinalSurrondings = [(), (), (), ()]
				# 	if row != 1 and grid[row - 2][column] != deathSpot:
				# 		slipCardinalSurrondings[0] = (row - 2, column)

				# 	if row != len(grid) - 2 and grid[row + 2][column] != deathSpot:
				# 		slipCardinalSurrondings[2] = (row + 2, column)

				# 	if column != 1 and grid[row][column - 2] != deathSpot:
				# 		slipCardinalSurrondings[3] = (row, column - 2)

				# 	if column != len(grid[0]) - 2 and grid[row][column + 2] != deathSpot:
				# 		slipCardinalSurrondings[1] = (row, column + 2)


				# 	# if it is a valid movement option (that won't just bump into the wall and have same movement restrictions
				# 	# as a non-slip move) then add rules to the solver as if it is a new starting point
				# 	for direction in range(len(slipCardinalSurrondings)):
				# 		if slipCardinalSurrondings[direction] != ():
				# 			pass
				# 			# findPath()
				# 			# solver.add(Implies(robotMovements[t][row][column], 
				# 			# 	Implies(mTypes[typeNum][direction], robotMovements[t + 1][slipCardinalSurrondings[direction][0]][slipCardinalSurrondings[direction][1]])))

				# 		# IMPORTANT
				# 		# can't have this else in case of wall bump, so specifically need no death square rule

				# 		# else:
				# 		# 	solver.add(Implies(robotMovements[t][row][column], Not(mTypes[typeNum][direction])))


				# THIS MUST BE POORLY APPLIED, FIX
				# # if already reached goal state, don't keep moving as that could result in player dying
				# if typeNum == int(goalSpot):
				# 	solver.add(Implies(robotMovements[t][row][column], robotMovements[t + 1][row][column]))


				# if it is a valid movement option, check which direction the spot you are on wants and do it
				# if it is an invalid direction, then record that that spot type cannot go in that direction
				for direction in range(len(cardinalSurrondings)):
					if cardinalSurrondings[direction] != ():
						solver.add(Implies(robotMovements[t][row][column], 
							Implies(mTypes[typeNum][direction], robotMovements[t + 1][cardinalSurrondings[direction][0]][cardinalSurrondings[direction][1]])))
					else:
						solver.add(Implies(robotMovements[t][row][column], Not(mTypes[typeNum][direction])))

	# on any turn, any of the goal states must be reached at least once
	solver.add(Or([ Or([turn[x[0]][x[1]] for x in goalList]) for turn in robotMovements]))

	return solver



s = Solver()

# the movement rules per tile type
# directions will be 1 north 2 east 3 south 4 west
movementTypes = [ [Bool(f"type{t}_direction{d}") for d in range(4)] for t in range(typeTotal)]

# only 1 allowable direction per type
s.add(And([Sum(x) == 1 for x in movementTypes]))

allMovements = [[[[ Bool(f"p{player}_square{x},{y}_turn{t}") for y in range(len(myGrid[x]))] for x in range(len(myGrid))] for t in range(X)] for player in range(len(startLocations))]
# run through each starting location to the goal location, creating rules as required
for start in range(len(startLocations)):
	s = findPath(startLocations[start], movementTypes, goalLocations, myGrid, s, allMovements[start])
	print(s.check())

# print once all the rules have been compiled together
for start in range(len(startLocations)):
	print("-------")
	print("On start location " + str(start))
	print(s.check())
	m = s.model()


	print("Start: " + str(startLocations[start]))
	goalReached = False
	for t in range(0, len(allMovements[start])):
		if not goalReached:
			for row in range(len(allMovements[start][t])):
				for column in range(len(allMovements[start][t][row])):
					if m[allMovements[start][t][row][column]]:
						print("Turn " + str(t + 1))
						print(row, column)

						if (row, column) in goalLocations:
							goalReached = True




# # locations in time for each starting point
# allMovements = [[[[ Bool(f"p{player}_square{x},{y}_turn{t}") for y in range(len(grid[x]))] for x in range(len(grid))] for t in range(X)] for player in range(len(startLocations))]

# for start in range(len(startLocations)):
# 	print("start " + str(startLocations[start]))
# 	# this will neeed to be in a loop over all start locations
# 	# now make a matrix the shape of the grid
# 	robotLocationBegin = [ [ BoolVal((x,y) == startLocations[start]) for y in range(len(grid[x]))] for x in range(len(grid))]

# 	# use the locations for this particular starting point
# 	robotMovements = allMovements[start]
# 	# robotMovements = [ [ [ Bool(f"square{x},{y}_turn{t}") for y in range(len(grid[x]))] for x in range(len(grid))] for t in range(X)]

# 	robotMovements = [robotLocationBegin] + robotMovements


# 	# the movement rules per tile type
# 	# directions will be 1 north 2 east 3 south 4 west
# 	movementTypes = [ [Bool(f"type{t}_direction{d}") for d in range(4)] for t in range(typeTotal)]

# 	# only 1 allowable direction per type
# 	solver.add(And([Sum(x) == 1 for x in movementTypes]))


# 	# movement rules

# 	# the player will only be in one location per turn
# 	for turn in robotMovements:
# 		solver.add(Sum([Sum(row) for row in turn]) == 1)

# 	# the movement will be in the cardinal directions
# 	for t in range(0, len(robotMovements) - 1):
# 		for row in range(len(robotMovements[t])):
# 			for column in range(len(robotMovements[row])):

# 				# the tile type at a particular location
# 				typeNum = int(grid[row][column])

# 				# get valid movement options
# 				# so no moving off the edge (since trying will mean eternally attempting to head off edge and thus never reaching goal)
# 				# no moving onto the death spots
# 				cardinalSurrondings = [(), (), (), ()]
# 				if row != 0 and grid[row - 1][column] != deathSpot:
# 					cardinalSurrondings[0] = (row - 1, column)
# 				if row != len(grid) - 1 and grid[row + 1][column] != deathSpot:
# 					cardinalSurrondings[2] = (row + 1, column)
# 				if column != 0 and grid[row][column - 1] != deathSpot:
# 					cardinalSurrondings[3] = (row, column - 1)
# 				if column != len(grid[0]) - 1 and grid[row][column + 1] != deathSpot:
# 					cardinalSurrondings[1] = (row, column + 1)

# 				# if it is a valid movement option, check which direction the spot you are on wants and do it
# 				# if it is an invalid direction, then record that that spot type cannot go in that direction
# 				for direction in range(len(cardinalSurrondings)):
# 					# if already reached goal state, don't keep moving as that could result in player dying
# 					if typeNum == int(goalSpot):
# 						solver.add(Implies(robotMovements[t][row][column], robotMovements[t + 1][row][column]))
# 					else:
# 						if cardinalSurrondings[direction] != ():
# 							# ice rules are different, so if moving in valid direction, may move 2
# 							if typeNum == int(iceSpot):
# 								pass
# 								# print("uhhh")
# 								# print(cardinalSurrondings)
# 								# print(direction)

# 								# if direction == 0:
# 								# 	print("north")
# 								# if direction == 1:
# 								# 	print("east")
# 								# if direction == 2:
# 								# 	print("south")
# 								# if direction == 3:
# 								# 	print("west")
# 								# needs to branch
# 								# needs to get recursive
# 								# so run same system pretty much, over new starting point that is normal cardinal
# 								# but also over one where the relavant direction has a step size 2 - which might also cause issues
# 								# of going out of range with the rows and columns again - guess calculate the cardinalSurrondings
# 								# with ice in mind already?
# 								# so move this section up
# 								# solver.add(Implies(robotMovements[t][row][column], 
# 								# 	Implies(movementTypes[typeNum][direction], robotMovements[t + 1][cardinalSurrondings[direction][0]][cardinalSurrondings[direction][1]])))
# 								# quit()
# 							else:
# 								solver.add(Implies(robotMovements[t][row][column], 
# 									Implies(movementTypes[typeNum][direction], robotMovements[t + 1][cardinalSurrondings[direction][0]][cardinalSurrondings[direction][1]])))
# 						else:
# 							solver.add(Implies(robotMovements[t][row][column], Not(movementTypes[typeNum][direction])))

# 	# on any turn, any of the goal states must be reached at least once
# 	solver.add(Or([ Or([turn[x[0]][x[1]] for x in goalLocations]) for turn in robotMovements]))




	# print("-------")
	# print("On start location " + str(start))
	# print(solver.check())
	# m = solver.model()


	# print("Start: " + str(startLocations[start]))
	# goalReached = False
	# for t in range(1, len(robotMovements)):
	# 	if not goalReached:
	# 		for row in range(len(robotMovements[t])):
	# 			for column in range(len(robotMovements[t][row])):
	# 				if m[robotMovements[t][row][column]]:
	# 					print("Turn " + str(t))
	# 					print(row, column)

	# 					if (row, column) in goalLocations:
	# 						goalReached = True

