def average(votes):
	import numpy

	if len(votes) == 0:
		return 0

	sigma_factor = 2.0
	avg = numpy.average(votes)
	sigma = numpy.std(votes) * sigma_factor

	corrected = []
	for vote in votes:
		if not (vote > avg + sigma or vote < avg - sigma):
			corrected.append(vote)

	ret = 0
	if len(corrected) > 0:
		ret = numpy.average(corrected)
		if numpy.isnan(ret):
			ret = 0

	return ret


def index(votes):
	def t(x):
		if x > 0:
			return 1 - (1.0/pow(x+1, 2))
		return 0

	interpolation = t(len(votes))
	return average(votes)*interpolation + 3*(1-interpolation)
