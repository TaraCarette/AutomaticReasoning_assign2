from z3 import Bool, BoolVal, Solver, And, Sum, Or, Not, Implies, If
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

man = {"name": "man", "num": 1, "weight": 1, "cannotOutnumber": [], "required": True}
wolf = {"name": "wolf", "num": 1, "weight": 1, "cannotOutnumber": ["goat"], "required": False}
goat = {"name": "goat", "num": 1, "weight": 1, "cannotOutnumber": ["cabbage"], "required": False}
cabbage = {"name": "cabbage", "num": 1, "weight": 1, "cannotOutnumber": [], "required": False}
beingsToCross = [man, wolf, goat, cabbage]

# get the total number of beings to cross
beingsTotal = sum([x["num"] for x in beingsToCross])


# setting up booleans for each being on each side for each timestep
leftSide = [[] for x in range(maxBoatCrossings)]
rightSide = [[] for x in range(maxBoatCrossings)]

# begin with all on the left, none on the right
for b in beingsToCross:
	leftSide[0] = leftSide[0] + [BoolVal(True) for x in range(b["num"])]
	rightSide[0] = rightSide[0] + [BoolVal(False) for x in range(b["num"])]

# rest will be assigned
for t in range(1, maxBoatCrossings):
	for b in beingsToCross:
		leftSide[t] = leftSide[t] + [Bool(f'{b["name"]}{x}_step{t}_left') for x in range(b["num"])]
		rightSide[t] = rightSide[t] + [Bool(f'{b["name"]}{x}_step{t}_right') for x in range(b["num"])]


# over all possible crossings, says if boat on left
# so false means boat is on the right
boatOnLeft = [BoolVal(x % 2 == 0) for x in range(maxBoatCrossings)]

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

# a being can only be one one side of the river at once
# also must be on at least 1 side
solver.add(And([Sum(leftSide[t][b], rightSide[t][b]) == 1 for b in range(len(leftSide[t])) for t in range(len(leftSide))]))


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
solver.add([(And(Implies(leftSide[t - 1][b], rightSide[t][b]), Implies(rightSide[t - 1][b], leftSide[t][b]))) for b in neededIndex for t in range(1, len(rightSide))])


# the side that has the boat for this timestep will have
# at least the minimum change to false, and no more than the maximum become false
solver.add([Implies(boatOnLeft[t - 1], Sum([leftSide[t - 1][b] != leftSide[t][b] for b in range(beingsTotal)]) <= maxPerBoat) for t in range(1, maxBoatCrossings)])
solver.add([Implies(boatOnLeft[t - 1], Sum([leftSide[t - 1][b] != leftSide[t][b] for b in range(beingsTotal)]) >= minPerBoat) for t in range(1, maxBoatCrossings)])

solver.add([Implies(Not(boatOnLeft[t - 1]), Sum([rightSide[t - 1][b] != rightSide[t][b] for b in range(beingsTotal)]) <= maxPerBoat) for t in range(1, maxBoatCrossings)])
solver.add([Implies(Not(boatOnLeft[t - 1]), Sum([rightSide[t - 1][b] != rightSide[t][b] for b in range(beingsTotal)]) >= minPerBoat) for t in range(1, maxBoatCrossings)])

# if boat did not move to this side at this timestep, nothing can switch to true
# (basically, only boat movement can allows being movement)
solver.add([Implies(Not(boatOnLeft[t]), Not(Or([And(Not(leftSide[t - 1][b]), leftSide[t][b]) for b in range(beingsTotal)]))) for t in range(1, maxBoatCrossings)])
solver.add([Implies(boatOnLeft[t], Not(Or([And(Not(rightSide[t - 1][b]), rightSide[t][b]) for b in range(beingsTotal)]))) for t in range(1, maxBoatCrossings)])


# some beings cannot be left alone with others safely
counter = 0
for b1 in beingsToCross:
	print(b1["name"])
	if b1["cannotOutnumber"] != []:
		b1Index = getBeingIndexes(b1["name"], beingsToCross)

		for b2 in b1["cannotOutnumber"]:
			b2Index = getBeingIndexes(b2, beingsToCross)

			solver.add([Sum([leftSide[t][b] for b in b1Index]) <= Sum([leftSide[t][b] for b in b2Index]) for t in range(maxBoatCrossings)])

print(solver.check())

m = solver.model()

# print initial states
print("Turn 0")
print("Boat LEFT")
counter = 0
for being in beingsToCross:
	for i in range(being["num"]):
		print(being["name"] + str(i) + " LEFT")


for t in range(1, maxBoatCrossings):
	print("--------------------")
	print("Turn " + str(t))

	if t%2 == 0:
		print("Boat LEFT")
	else:
		print("Boat RIGHT")
	counter = 0
	for being in beingsToCross:
		for i in range(being["num"]):
			if m[leftSide[t][counter]]:
				print(being["name"] + str(i) + " LEFT")
			elif m[rightSide[t][counter]]:
				print(being["name"] + str(i) + " RIGHT")
			else:
				print("problem")

			counter += 1



# # if all beings are on the right side before the final timestep, just stay there
# solver.add([(Implies(And([x for x in rightSide[t - 1]]), And([x for x in rightSide[t]]))) for t in range(1, len(rightSide))])

# all beings must be on the right side by the end
# solver.add(And(rightSide[-1]))


# # only the max weight of beings switch sides (as boat can only hold that much)
# possibleBoatCombos = []
# for t in range(1, len(rightSide)):
# 	for subset in itertools.combinations(leftSide[t], maxPerBoat):
# 		ind1 = leftSide[t].index(subset[0])
# 		ind2 = leftSide[t].index(subset[1])
# 		possibleBoatCombos.append(And(subset[0] == Not(leftSide[t - 1][ind1]), subset[1] == Not(leftSide[t - 1][ind2])))