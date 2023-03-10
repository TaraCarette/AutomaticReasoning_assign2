from z3 import Bool, BoolVal, Solver, And, Sum, Or, Not, Implies
import itertools

# river crossing problem

maxWeightPerBoat = 2
maxPerBoat = 2
minPerBoat = 1


maxBoatCrossings = 10

# define types based on: 
# how many there are
# how much they weigh
# which group they cannot outnumber
# required to be on boat (like the man guiding it)

# man = {"name": "man", "num": 1, "weight": 1, "cannotOutnumber": [], "required": True}
# wolf = {"name": "wolf", "num": 1, "weight": 1, "cannotOutnumber": ["goat"], "required": False}
# goat = {"name": "goat", "num": 1, "weight": 1, "cannotOutnumber": ["cabbage"], "required": False}
# cabbage = {"name": "cabbage", "num": 1, "weight": 1, "cannotOutnumber": [], "required": False}
# beingsToCross = [man, wolf, goat, cabbage]

smallRobot = {"name": "smallRobot", "num": 2, "weight": 1, "cannotOutnumber": [], "required": False}
largeRobot = {"name": "largeRobot", "num": 2, "weight": 2, "cannotOutnumber": [], "required": False}
beingsToCross = [smallRobot, largeRobot]

# get the total number of beings to cross
beingsTotal = sum([x["num"] for x in beingsToCross])


# setting up booleans for each being on each side for each timestep
leftSide = [[] for x in range(maxBoatCrossings + 1)]
rightSide = [[] for x in range(maxBoatCrossings + 1)]

# begin with all on the left, none on the right
for b in beingsToCross:
	leftSide[0] = leftSide[0] + [BoolVal(True) for x in range(b["num"])]
	rightSide[0] = rightSide[0] + [BoolVal(False) for x in range(b["num"])]

# rest will be assigned
for t in range(1, maxBoatCrossings + 1):
	for b in beingsToCross:
		leftSide[t] = leftSide[t] + [Bool(f'{b["name"]}{x}_step{t}_left') for x in range(b["num"])]
		rightSide[t] = rightSide[t] + [Bool(f'{b["name"]}{x}_step{t}_right') for x in range(b["num"])]


# over all possible crossings, says if boat on left
# so false means boat is on the right
boatOnLeft = [BoolVal(x % 2 == 0) for x in range(maxBoatCrossings + 1)]

# for now, no rules about who can be on the boat together, since for now always with man, switch later

solver = Solver()


def getBeingIndexes(name, beingsToCross):
	requiredIndex = []
	counter = 0
	for b in beingsToCross:
		if b["name"] == name:
			for i in range(b["num"]):
				requiredIndex.append(counter + i)

		counter += b["num"]

	return requiredIndex

def getNameFromIndex(ind, beingsToCross):
	counter = 0
	name = None
	for b in beingsToCross:
		counter += b["num"]

		if ind < counter:
			name = b["name"]
			break

	return name


# a being can only be one one side of the river at once
# also must be on at least 1 side
solver.add(And([Sum(leftSide[t][b], rightSide[t][b]) == 1 for b in range(len(leftSide[t])) for t in range(maxBoatCrossings + 1)]))


# there must be a point where everyone is on the right side
# (as problem is symmetric, will not result in a failure if allowed to keep moving, so can ignore if takes
# less turns than given to achieve this)
solver.add(Or([And(rightSide[t]) for t in range(len(rightSide))]))


# if a being is required on the boat, it must switch sides every turn
# get the index of every required being
neededIndex = []
counter = 0
for b in beingsToCross:
	if b["required"]:
		neededIndex = neededIndex + getBeingIndexes(b["name"], beingsToCross)

# make sure those beings switch sides
solver.add([(And(Implies(leftSide[t - 1][b], rightSide[t][b]), Implies(rightSide[t - 1][b], leftSide[t][b]))) for b in neededIndex for t in range(1, maxBoatCrossings + 1)])


# the side that has the boat for this timestep will have
# at least the minimum change to false, and no more than the maximum become false
solver.add([Implies(boatOnLeft[t - 1], Sum([leftSide[t - 1][b] != leftSide[t][b] for b in range(beingsTotal)]) <= maxPerBoat) for t in range(1, maxBoatCrossings + 1)])
solver.add([Implies(boatOnLeft[t - 1], Sum([leftSide[t - 1][b] != leftSide[t][b] for b in range(beingsTotal)]) >= minPerBoat) for t in range(1, maxBoatCrossings + 1)])

solver.add([Implies(Not(boatOnLeft[t - 1]), Sum([rightSide[t - 1][b] != rightSide[t][b] for b in range(beingsTotal)]) <= maxPerBoat) for t in range(1, maxBoatCrossings + 1)])
solver.add([Implies(Not(boatOnLeft[t - 1]), Sum([rightSide[t - 1][b] != rightSide[t][b] for b in range(beingsTotal)]) >= minPerBoat) for t in range(1, maxBoatCrossings + 1)])

# if boat did not move to this side at this timestep, nothing can switch to true
# (basically, only boat movement can allows being movement)
solver.add([Implies(Not(boatOnLeft[t]), Not(Or([And(Not(leftSide[t - 1][b]), leftSide[t][b]) for b in range(beingsTotal)]))) for t in range(1, maxBoatCrossings + 1)])
solver.add([Implies(boatOnLeft[t], Not(Or([And(Not(rightSide[t - 1][b]), rightSide[t][b]) for b in range(beingsTotal)]))) for t in range(1, maxBoatCrossings + 1)])


# some beings cannot be left alone with others safely
counter = 0
for b1 in beingsToCross:
	if b1["cannotOutnumber"] != []:
		b1Index = getBeingIndexes(b1["name"], beingsToCross)

		for b2 in b1["cannotOutnumber"]:
			b2Index = getBeingIndexes(b2, beingsToCross)

			# if boat not there to supervise, then make sure no bad pairings
			solver.add([Implies(Not(boatOnLeft[t]), Or(Sum([leftSide[t][b] for b in b1Index]) < Sum([leftSide[t][b] for b in b2Index]), Sum([leftSide[t][b] for b in b2Index]) == 0)) for t in range(maxBoatCrossings + 1)])
			solver.add([Implies(boatOnLeft[t], Or(Sum([rightSide[t][b] for b in b1Index]) < Sum([rightSide[t][b] for b in b2Index]), Sum([rightSide[t][b] for b in b2Index]) == 0)) for t in range(maxBoatCrossings + 1)])



# the beings on the boat must not go over the weight limit
# so on a side, these combos cannot go from true to false 
# (aka, getting on boat together) as they are over the weight limit
for t in range(1, len(rightSide)):
	for subset in itertools.combinations(leftSide[t], maxPerBoat):
		weight = 0
		for i in range(maxPerBoat):
			ind = leftSide[t].index(subset[i])
			name = getNameFromIndex(ind, beingsToCross)

			for b in beingsToCross:
				if b["name"] == name:
					weight += b["weight"]

		if weight > maxWeightPerBoat:
			if t > 1:
				solver.add(Not(And([And(leftSide[t - 1][leftSide[t].index(subset[x])], Not(leftSide[t][leftSide[t].index(subset[x])])) for x in range(maxPerBoat)])))

			else:
				solver.add(Not(And([And(leftSide[t - 1][0], Not(x)) for x in subset])))

print(solver.check())

m = solver.model()

# print initial states
print("Turn 0")
print("Boat LEFT")
counter = 0
for being in beingsToCross:
	for i in range(being["num"]):
		print(being["name"] + str(i) + " LEFT")


for t in range(1, maxBoatCrossings + 1):
	print("--------------------")
	print("Turn " + str(t))

	if t%2 == 0:
		print("Boat LEFT")
	else:
		print("Boat RIGHT")
	counter = 0
	crossCounter = 0
	for being in beingsToCross:
		for i in range(being["num"]):
			if m[leftSide[t][counter]]:
				print(being["name"] + str(i) + " LEFT")
			if m[rightSide[t][counter]]:
				print(being["name"] + str(i) + " RIGHT")
				crossCounter += 1

			counter += 1

	if crossCounter == beingsTotal:
		print("Crossed!")
		break

