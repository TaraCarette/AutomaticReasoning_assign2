from z3 import Bool, BoolVal, Solver, And, Sum, Implies, Or, Not
import csv

gridFile = "demogrid.csv"
# gridFile = "grid1.csv"
# gridFile = "grid2.csv"
X = 11

# numbers of meaningful spots
# other numbers just indicate when types match, nothing else
startSpot = "0"
goalSpot = "1"
deathSpot = "2"
iceSpot = "3"



def read_grid(filename):
  with open(filename, 'r') as file:
    # Return a reader object which will
    # iterate over lines in the given csvfile
    grid_reader = csv.reader(file)
    
    # convert string to list
    grid = list(grid_reader)
    return grid

myGrid = read_grid(gridFile) 
# get the total number of types in the grid
typeTotal = max([max([int(x) for x in y]) for y in myGrid]) + 1

startLocations = []
for row in range(len(myGrid)):
	for column in range(len(myGrid[row])):
		if myGrid[row][column] == startSpot:
			startLocations.append((row, column))

# TEMPORARY
startLocations = [startLocations[1]]

# the list of goal states that can be reached
goalLocations = []
for row in range(len(myGrid)):
	for column in range(len(myGrid[row])):
		if myGrid[row][column] == goalSpot:
			goalLocations.append((row, column))




def findPath(startLoc, mTypes, goalList, grid, solver, robotMovements, player):
	# robot is placed for the first turn
	# afterwards, will they can merge, no more can be created
	# for turn in robotMovements:
	# 	solver.add(Sum([Sum(row) for row in turn]) == 1)

	# for each spot in time, the movement will be guided by the
	# tile type
	# avoiding death tiles
	# avoiding edges
	for t in range(1, len(robotMovements)):
		for row in range(len(robotMovements[t])):
			for column in range(len(robotMovements[row])):

				# for each spot, check where it could have possibly come from
				# needs to be in reverse order to correspond which direction it needs to
				# go to get to the target spot. so a south spot should be stored in the north spot in mTypes
				cardinalSurrondings = [(), (), (), ()]
				if row != 0:
					cardinalSurrondings[2] = (row - 1, column)

				if row != len(grid) - 1:
					cardinalSurrondings[0] = (row + 1, column)

				if column != 0:
					cardinalSurrondings[1] = (row, column - 1)

				if column != len(grid[0]) - 1:
					cardinalSurrondings[3] = (row, column + 1)


				# the tile type at a particular location
				typeNum = int(grid[row][column])


				# for each cardinally surronding spot, add the type and the relevant value to the list
				# of possibilities allowing the current spot to become true
				possibleMovements = []
				for direction in range(len(cardinalSurrondings)):
					# can be true because a neighbour moved in this direction, and
					#  neighbour not goal (never move off goal state once reached)
					if cardinalSurrondings[direction] != ():
						neighborTypeNum = int(grid[cardinalSurrondings[direction][0]][cardinalSurrondings[direction][1]])

						# if neighbour is a goal spot, this spot cannot become true through it
						if neighborTypeNum != int(goalSpot):
							possibleMovements.append(And(mTypes[neighborTypeNum][direction], robotMovements[t - 1][cardinalSurrondings[direction][0]][cardinalSurrondings[direction][1]]))

					elif typeNum == int(goalSpot):
						# can also be true because was on goal state las time and should stay there
						possibleMovements.append(robotMovements[t - 1])

					else:
						# can be true because it was already here and tried to move on an edge
						# direction gets reversed as frame of reference now current square, not neighbor going to current
						reversedDirection = (direction + 2) % 4
						possibleMovements.append(And(mTypes[typeNum][reversedDirection], robotMovements[t - 1][row][column]))




				# # if this is a death spot, make sure none of the corresponding possibilities are true
				# if typeNum == int(deathSpot):
				# 	solver.add(Not(Or(possibleMovements)))


				# this space is true iff on the previous turn there was a robot in the right
				# place with the required tile direction	
				solver.add(robotMovements[t][row][column] == Or(possibleMovements))




	# nothing on a not goal state
	for row in range(len(robotMovements[0])):
		for column in range(len(robotMovements[0])):
			if not (row, column) in goalList:
				solver.add(Not(robotMovements[-1][row][column]))


	# need to make sure cannot disapear, then get rid of this rule
	# solver.add(Or(robotMovements[-1][goalList[0][0]][goalList[0][1]], robotMovements[-1][goalList[1][0]][goalList[1][1]]))
	# solver.add(Or([ Or([turn[x[0]][x[1]] for x in goalList]) for turn in robotMovements]))

	return solver



s = Solver()

# the movement rules per tile type
# directions will be 1 north 2 east 3 south 4 west
movementTypes = [ [Bool(f"type{t}_direction{d}") for d in range(4)] for t in range(typeTotal)]

# only 1 allowable direction per type (allow less so can set goal to no direction as should stop moving)
s.add(And([Sum(x) == 1 for x in movementTypes]))

allMovements = [[[[ Bool(f"p{player}_square{x},{y}_turn{t}") for y in range(len(myGrid[x]))] for x in range(len(myGrid))] for t in range(X)] for player in range(len(startLocations))]
# run through each starting location to the goal location, creating rules as required
for start in range(len(startLocations)):
	# print(startLocations[start])
	# for these start locations, we already know where the robot begins its first turn
	robotLocationBegin = [ [ BoolVal((x,y) == startLocations[start]) for y in range(len(myGrid[x]))] for x in range(len(myGrid))]
	rMovements = [robotLocationBegin] + allMovements[start]

	s = findPath(startLocations[start], movementTypes, goalLocations, myGrid, s, rMovements, start)
	print(s.check())

# print once all the rules have been compiled together
for start in range(len(startLocations)):
	print("-------")
	print("On start location " + str(start))
	print(s.check())
	m = s.model()

	# print([[x for x in y] for y in movementTypes])
	# print([[m[x] for x in y] for y in movementTypes])

	print("Start: " + str(startLocations[start]))
	goalReached = False
	for t in range(0, len(allMovements[start])):
		# if not goalReached:
		print("Turn " + str(t + 1))
		for row in range(len(allMovements[start][t])):
			for column in range(len(allMovements[start][t][row])):
				if m[allMovements[start][t][row][column]]:
					print(row, column)

					if (row, column) in goalLocations:
						goalReached = True
						print("goal reached")





