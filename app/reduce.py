#!/bin/python3

import os, sys, platform
from datetime import datetime

def main():
   timenow = datetime.now().strftime("%H:%M:%S")
   print(f'Running reduce on host "{platform.node()}" at {timenow}.')

if __name__ == "__main__":
	main()

