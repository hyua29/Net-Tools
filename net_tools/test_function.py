import getopt
import sys


opt, args = getopt.getopt(sys.argv[1:], "hl", ["help"], ["listen"])

print(opt)