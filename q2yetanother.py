from z3 import Bool, BoolVal, Solver, And, Sum, Implies, Or, Not
import csv

# gridFile = "demogrid.csv"
gridFile = "grid1.csv"
# gridFile = "grid2.csv"
# gridFile = "grid3.csv"
X = 20

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


# extract the starting locations from the grid
startLocations = []
for row in range(len(myGrid)):
	for column in range(len(myGrid[row])):
		if myGrid[row][column] == startSpot:
			startLocations.append((row, column))

# the list of goal states that can be reached
goalLocations = []
for row in range(len(myGrid)):
	for column in range(len(myGrid[row])):
		if myGrid[row][column] == goalSpot:
			goalLocations.append((row, column))



def findPath(mTypes, goalList, grid, solver, robotMovements):
	# for each tile, decides if a robot can be present based on previous
	# timestep and the relationship between the tiles
	# this allows for the robots to split onto multiple paths
	# and works as we know the starting locations
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


				# get the ice surrondings as well, only the double step
				# as the normal step is already covered by the normal case
				slipCardinalSurrondings = [(), (), (), ()]
				if row > 1:
					slipCardinalSurrondings[2] = (row - 2, column)

				if row < len(grid) - 2:
					slipCardinalSurrondings[0] = (row + 2, column)

				if column > 1:
					slipCardinalSurrondings[1] = (row, column - 2)

				if column < len(grid[0]) - 2:
					slipCardinalSurrondings[3] = (row, column + 2)


				# the tile type at this particular location
				typeNum = int(grid[row][column])


				# for each cardinally surronding spot, add the relevant direction of the type of spot
				# (so if tile 4 is below the target, we take the value of 4 north)
				# and if the robot was in the adjacent spot the previous timestep
				# to the list of possibilities allowing the current spot to become true
				possibleMovements = []
				for direction in range(len(cardinalSurrondings)):
					# can be true because a neighbour moved in this direction
					if cardinalSurrondings[direction] != ():
						neighborTypeNum = int(grid[cardinalSurrondings[direction][0]][cardinalSurrondings[direction][1]])

						# if neighbour is a goal spot, this spot cannot become true through it as no longer moves once hits goal
						if neighborTypeNum != int(goalSpot):
							possibleMovements.append(And(mTypes[neighborTypeNum][direction], robotMovements[t - 1][cardinalSurrondings[direction][0]][cardinalSurrondings[direction][1]]))

					else:
						# can be true because it was already here and tried to move on an edge
						# direction gets reversed as frame of reference now current square, not neighbor going to current
						reversedDirection = (direction + 2) % 4
						possibleMovements.append(And(mTypes[typeNum][reversedDirection], robotMovements[t - 1][row][column]))


				# check the ice neighbours to see if that possibility works as well
				for direction in range(len(slipCardinalSurrondings)):
					# can be true because a neighbour moved in this direction, and
					#  neighbour not goal (never move off goal state once reached)
					if slipCardinalSurrondings[direction] != ():
						neighborTypeNum = int(grid[slipCardinalSurrondings[direction][0]][slipCardinalSurrondings[direction][1]])

						# only if neighbour is ice spot can it come from here
						if neighborTypeNum == int(iceSpot):
							possibleMovements.append(And(mTypes[neighborTypeNum][direction], robotMovements[t - 1][slipCardinalSurrondings[direction][0]][slipCardinalSurrondings[direction][1]]))


				# if last time spot was true and a is goal spot, it stays true
				if typeNum == int(goalSpot):
					# can also be true because was on goal state las time and should stay there
					possibleMovements.append(robotMovements[t - 1][row][column])



				# if this is a death spot, make sure none of the corresponding possibilities are true
				if typeNum == int(deathSpot):
					solver.add(Not(Or(possibleMovements)))


				# this space is true iff on the previous turn there was a robot in the right
				# place with the required tile direction	
				solver.add(robotMovements[t][row][column] == Or(possibleMovements))




	# nothing on a not goal state at the final timestep
	# robots cannot disappear and so they must all be on a goal state
	for row in range(len(robotMovements[0])):
		for column in range(len(robotMovements[0])):
			if not (row, column) in goalList:
				solver.add(Not(robotMovements[-1][row][column]))


	return solver



s = Solver()

# the movement rules per tile type
# directions will be 0 north 1 east 2 south 3 west
movementTypes = [ [Bool(f"type{t}_direction{d}") for d in range(4)] for t in range(typeTotal)]

# only 1 allowable direction per type
s.add(And([Sum(x) == 1 for x in movementTypes]))


# create a grid with all the timesteps for each starting spot
allMovements = [[[[ Bool(f"p{player}_square{x},{y}_turn{t}") for y in range(len(myGrid[x]))] for x in range(len(myGrid))] for t in range(X)] for player in range(len(startLocations))]

# run through each starting location to the goal location, creating rules as required
for start in range(len(startLocations)):
	# for these start locations, we already know where the robot begins its first turn
	robotLocationBegin = [ [ BoolVal((x,y) == startLocations[start]) for y in range(len(myGrid[x]))] for x in range(len(myGrid))]
	rMovements = [robotLocationBegin] + allMovements[start]

	s = findPath(movementTypes, goalLocations, myGrid, s, rMovements)
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
		print("Turn " + str(t + 1))
		for row in range(len(allMovements[start][t])):
			for column in range(len(allMovements[start][t][row])):
				if m[allMovements[start][t][row][column]]:
					print(row, column)

					if (row, column) in goalLocations:
						goalReached = True





