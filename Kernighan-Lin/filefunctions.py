def getFile(fileName):
	lines = open(fileName).read().split('\n')
	print 'File ' + fileName + ' opened'
	return lines

def parseFile(lines):
	del lines[0:2]
	if lines[-1] == ' ' or '\n' or '/n':
		del lines[-1]
	return lines

def writeFile(filename,result):

	filename = open(filename,'w')
	cutsetsize = str(result[0])
	A = result[1]
	B = result[2]
	filename.write(cutsetsize+'\n')
	for node in range(0,len(A)-1):
		filename.write(str(A[node]+1)+',')
	filename.write(str(A[-1]+1))
	filename.write('\n')
	for node in range(0,len(B)-1):
		filename.write(str(B[node]+1)+',')
	filename.write(str(B[-1]+1))
	filename.close()




