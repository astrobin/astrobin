from bin.models import Subject

for m in range(1, 110):
	s = Subject(name="M"+str(m))
	s.save()
